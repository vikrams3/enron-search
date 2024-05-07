# enron-search
Type-ahead Search Engine with Auto-Complete for Textual Big Data

Some brief design decisions:
1) to serialize the node array, I am using Python's basic array module that gives C-like access to primitive types (4 bytes for int).
2) keeping track of email_ids (integers) as a separate serialized file. No limit on the number of email_ids that can be stored.
3) disk seek() is being done with an offset of 32 ints for every node in the serialized file.
4) in addition to child offsets, every trie node has some bookkeeping info such as: isLeaf, isEndOfWord, offset into email_id file, size of email_ids for this node. The last two are valid only if the node is end of word.
5) filters out stop-words from the trie (such as "the", "than" etc.)
6) using BFS to serialize the trie, and DFS after the prefix has been matched to suggest auto-completion words.

Performance numbers: The dataset has 517,401 email files. Took 20 mins to build a trie on my MacBook Pro on the entire dataset (2.2 GHz, 6-Core Intel Core i7, 16 GB RAM).

Here is a sample run with 12 randomly selected email files. You may change the FILE_PREFIX to run on your own machine. Please take a look at the attached code.

```
VIKSUBRA-M-83ZG:project viksubra$ python3 enron_search.py
Step 1: Built the trie!
Step 2_1: Serialized trie to:  /Users/viksubra/git/codeprep/apple/serialized_trie.bin
Step 2_2: Serialized email ids to:  /Users/viksubra/git/codeprep/apple/serialized_email_ids.bin
Step 3: Now, ready to search via file seek() of serialized trie
-------------------
Searching for prefix:  really
{'really': ['maildir/arnold-j/notes_inbox/36.']}
-------------------
Searching for prefix:  th
{'thanks': ['maildir/scholtes-d/stf/8.',
            'maildir/stclair-c/sent/2315.',
            'maildir/stclair-c/sent/650.'],
 'thing': ['maildir/arnold-j/notes_inbox/36.'],
 'think': ['maildir/stclair-c/sent/2315.',
           'maildir/stclair-c/sent/324.',
           'maildir/stclair-c/sent/650.',
           'maildir/stclair-c/sent/594.'],
 'thought': ['maildir/scholtes-d/stf/18.'],
 'thoughts': ['maildir/stclair-c/sent/324.', 'maildir/stclair-c/sent/594.'],
 'threshold': ['maildir/stclair-c/sent/324.'],
 'thu': ['maildir/arnold-j/notes_inbox/36.',
         'maildir/scholtes-d/stf/12.',
         'maildir/stclair-c/sent/594.'],
 'thursday': ['maildir/stclair-c/sent/2315.']}
-------------------
Searching for prefix:  cont
{'contact': ['maildir/arnold-j/notes_inbox/50.',
             'maildir/stclair-c/sent/2315.'],
 'contains': ['maildir/stclair-c/sent/324.'],
 'contracts': ['maildir/arnold-j/notes_inbox/50.']}
-------------------
Searching for prefix:  than
{'thanks': ['maildir/scholtes-d/stf/8.',
            'maildir/stclair-c/sent/2315.',
            'maildir/stclair-c/sent/650.']}
-------------------
Searching for prefix:  mar
{'mark': ['maildir/arnold-j/notes_inbox/36.'],
 'marketing': ['maildir/arnold-j/notes_inbox/50.']}
-------------------
Searching for prefix:  sto
[]
-------------------
Done! :-)
```
