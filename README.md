# statls
list files in hidden directories with --x permissions

Example below:
```
$ ls -la
total 0
drwxr-xr-x   3 demo  staff  102 Sep 13 23:18 .
drwxr-xr-x  15 demo  staff  510 Sep 13 23:18 ..
d--x--x--x   2 demo  staff   68 Sep 13 23:17 hiddendir
$ cd hiddendir/
hiddendir$ ls
ls: .: Permission denied
hiddendir$ statls.py -f qqq "."
1
d--x--x--x   6   501    20        204  Tue Sep 13 23:22:37 2016  .
42
drwxr-xr-x   3   501    20        102  Tue Sep 13 23:18:40 2016  ..
41311
-rw-r--r--   1   501    20         36  Tue Sep 13 23:35:19 2016  tst
hiddendir$ cat tst
I cant believe you found this file!

```

Awesome! Right. Now you should stop serving your public_html from your home directory ;)
