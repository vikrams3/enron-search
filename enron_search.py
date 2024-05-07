# author: Vikram Subramanya
# Date: 05/26/2020
# Trie inspired from https://www.geeksforgeeks.org/trie-insert-and-search/

import sys
import pprint
import array  # to efficiently represent ints in the serialized array

FILE_PREFIX = '/Users/viksubra/git/codeprep/apple/'
EMAIL_LIST_FILENAME = 'email_files_12.py'
SERIALIZED_TRIE_FILENAME = 'serialized_trie.bin'
SERIALIZED_EMAIL_IDS_FILENAME = 'serialized_email_ids.bin'

NUM_ALPHABETS = 26
END_OF_WORD_IDX = 26  # is the given node end of a word?
IS_LEAF_IDX = 27      # is the given node a leaf?
EMAIL_IDS_OFFSET_IDX = 28  # stores the start offset into email_ids_file.
EMAIL_IDS_SIZE_IDX = 29  # stores the number of email ids corresponding to word.
# 26 alphabet offsets, 1 int each for endOfWord, isLeaf + 4 ints for future use
SERIALIZED_NODE_SIZE = 32
# from nltk.corpus import stopwords
STOPWORDS = {
    'ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about',
    'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be',
    'some', 'for', 'do', 'its', 'yours', 'such', 'into', 'of', 'most', 'itself',
    'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each',
    'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his',
    'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this',
    'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to',
    'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them',
    'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does', 'yourselves',
    'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not',
    'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too',
    'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't',
    'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it',
    'how', 'further', 'was', 'here', 'than'
}

class TrieNode:
    def __init__(self, character):
        self.character = character
        self.children = {}  # map of child chars to child node pointers
        self.isEndOfWord = False  # if node represents the end of the word
        # stores all email ids (indexes into email_files) in which word is found.
        # It is populated only if isEndOfWord is True
        self.email_ids = array.array('i') 

def charToInt(ch):
    return ord(ch) - ord('a')
def intToChar(i):
    return chr(ord('a') + i)

class Trie:
    def __init__(self):
        self.root = TrieNode('0')

    def insert(self, word, email_id):
        node = self.root 
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode(ch)
            node = node.children[ch]
        node.isEndOfWord = True
        node.email_ids.append(email_id)

    def serialize(self):
        '''
        Perform level-order traversal on trie and serialize every node into
        32 integers. Each alphabet will have child node's offset if present.
        The endOfWord node will have a marker and a file offset into
        email_list_file that will store emails in which word is found. Leaf node
        will also have a marker.
        '''
        def getByteOffset(arr, arr_idx):
            return arr_idx * arr.itemsize

        if self.root is None: 
            return
        serialized_trie = array.array('i')
        serialized_trie.fromlist([0 for _ in range(SERIALIZED_NODE_SIZE)])
        serialized_email_ids = array.array('i')

        # queue contains a tuple of
        # (node of trie, start index in the serialized_trie)
        queue = []
        queue.append((self.root, 0))

        while(len(queue) > 0):
            parent, parent_idx = queue.pop(0)
            if parent.isEndOfWord:
                serialized_trie[parent_idx + END_OF_WORD_IDX] = 1
                # populate email ids into serialized array
                email_id_idx = len(serialized_email_ids)
                serialized_email_ids.extend(parent.email_ids)
                serialized_trie[parent_idx + EMAIL_IDS_OFFSET_IDX] = \
                    getByteOffset(serialized_email_ids, email_id_idx)
                serialized_trie[parent_idx + EMAIL_IDS_SIZE_IDX] = \
                    len(parent.email_ids)

            if len(parent.children) == 0:
                serialized_trie[parent_idx + IS_LEAF_IDX] = 1
            for ch, child in parent.children.items():
                # since we're doing level-order, we're seeing child for the
                # first time. So create a new serialized array for the child
                serialized_child = [0 for _ in range(SERIALIZED_NODE_SIZE)]
                child_idx = len(serialized_trie)
                # extend serialized_trie with the child's serialized array
                serialized_trie.fromlist(serialized_child)
                # update parent node's child offset value
                parent_child_idx = parent_idx + charToInt(ch)
                serialized_trie[parent_child_idx] = \
                    getByteOffset(serialized_trie, child_idx)
                queue.append((child, child_idx))

        # write serialized_trie to disk
        with open(FILE_PREFIX + SERIALIZED_TRIE_FILENAME, 'wb') as fp:
            serialized_trie.tofile(fp)
        # write serialized_email_ids to disk
        with open(FILE_PREFIX + SERIALIZED_EMAIL_IDS_FILENAME, 'wb') as fp:
            serialized_email_ids.tofile(fp)

class PrefixSearcher:
    '''
    Reads serialized files via disk seeks for search.
    email_files is a list of email files in the dataset.
    '''
    def __init__(self, email_files):
        self.trie_file = FILE_PREFIX + SERIALIZED_TRIE_FILENAME
        self.email_ids_file = FILE_PREFIX + SERIALIZED_EMAIL_IDS_FILENAME
        self.email_files = email_files

    def _dfs(self, trie_fp, email_ids_fp, serialized_node, slate, res):
        '''Recursively perform DFS on the node; update slate with full words'''
        if serialized_node[END_OF_WORD_IDX] == 1:
            email_ids_offset = serialized_node[EMAIL_IDS_OFFSET_IDX]
            email_ids_size = serialized_node[EMAIL_IDS_SIZE_IDX]
            email_ids_fp.seek(email_ids_offset)
            serialized_email_ids = array.array('i')
            serialized_email_ids.fromfile(email_ids_fp, email_ids_size)
            matching_word = ''.join(slate)
            res[matching_word] = []
            for email_id in serialized_email_ids:
                res[matching_word].append(self.email_files[email_id].strip())
        if serialized_node[IS_LEAF_IDX] == 1:
            return

        for i in range(NUM_ALPHABETS):
            child_offset = serialized_node[i]
            if child_offset == 0:
                continue
            slate.append(intToChar(i))
            trie_fp.seek(child_offset)
            serialized_child = array.array('i')
            serialized_child.fromfile(trie_fp, SERIALIZED_NODE_SIZE)
            self._dfs(trie_fp, email_ids_fp, serialized_child, slate, res)
            slate.pop()

    def search(self, prefix):
        res = {}
        serialized_node = array.array('i')
        with open(self.trie_file, 'rb') as trie_fp:
            serialized_node.fromfile(trie_fp, SERIALIZED_NODE_SIZE)
            for ch in prefix:
                # set the new offset to the child's offset. Bail out if child
                # node doesn't exist i.e. prefix not present.
                offset = serialized_node[charToInt(ch)]
                if offset == 0:
                    return []
                # seek() into the child offset
                trie_fp.seek(offset)
                del serialized_node[:]
                serialized_node.fromfile(trie_fp, SERIALIZED_NODE_SIZE)
            with open(self.email_ids_file, 'rb') as email_ids_fp:
                self._dfs(trie_fp, email_ids_fp, serialized_node, list(prefix), res)
        return res

def preprocess():
    email_files = None
    with open(FILE_PREFIX + EMAIL_LIST_FILENAME) as fp:
        t = Trie()
        # stores all email file names in memory, for use in search results
        email_files = fp.readlines()
        for email_id, email_file in enumerate(email_files):
            # print('processing email: ', email_filepath)
            with open(FILE_PREFIX + email_file.strip(), errors='ignore') as fp:
                try:
                    lines = fp.readlines()
                except:
                    print('Exception occured in file: ', email_file)
                    continue
                added_words = set()
                for line in lines:
                    line = line.strip()
                    words = line.split(' ')
                    for word in words:
                        word = word.strip(',.!()*?/\'"')
                        word = word.lower()
                        if (word.isalpha() and word not in STOPWORDS
                            and word not in added_words):
                            added_words.add(word)
                            t.insert(word, email_id)
        print('Step 1: Built the trie!')
        t.serialize()
        print('Step 2_1: Serialized trie to: ',
              FILE_PREFIX + SERIALIZED_TRIE_FILENAME)
        print('Step 2_2: Serialized email ids to: ',
              FILE_PREFIX + SERIALIZED_EMAIL_IDS_FILENAME)
    return email_files

def main():
    email_files = preprocess()
    ps = PrefixSearcher(email_files)
    print('Step 3: Now, ready to search via file seek() of serialized trie')
    print('-------------------')
    searchPrefixes = ['really', 'th', 'cont', 'than', 'mar', 'sto']
    for sp in searchPrefixes:
        print('Searching for prefix: ', sp)
        pprint.pprint(ps.search(sp))
        print('-------------------')
    print('Done! :-)')

if __name__ == '__main__': 
    main()