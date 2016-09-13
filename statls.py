#!/usr/bin/env python

import os, string, getopt, sys
from stat import *
import time

charset_default = list(string.lowercase + string.uppercase + string.digits + "._-~")
charset_quick = list("._-~" + string.lowercase + string.digits)
extentions = ['.tar', '.tar.gz', '.zip', '.gz', '.sql']


# colors
class fgcolors:
    normal = "\033[0m"
    blink = "\033[5m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"
    white = "\033[37m"
    red = "\033[31m"
    green = "\033[32m"
    pink = "\033[35m\033[1m"
    brown = "\033[33m"


fgcolor = fgcolors()
# ls lookalike
permission_format_map = [S_IRUSR, S_IWUSR, S_IXUSR, S_IRGRP, S_IWGRP, S_IXGRP, S_IROTH, S_IWOTH, S_IXOTH]
permission_format_text = [('-', 'r'), ('-', 'w'), ('-', 'x'), ('-', 'r'), ('-', 'w'), ('-', 'x'), ('-', 'r'),
                          ('-', 'w'), ('-', 'x')]


def build_permission(st):
    output = []
    output.append(('-', 'd')[S_ISDIR(st.st_mode)])
    for permission, mapping in zip(permission_format_map, permission_format_text):
        if permission & st.st_mode:
            mode = 1
        else:
            mode = 0
        output.append(mapping[mode])
    return string.join(output, '')


def prettyreport(filename, st):
    permission = build_permission(st)
    # format filename with a color ?
    args = {'permission': permission, 'size': st.st_size, 'uid': st.st_uid, 'gid': st.st_gid, 'nlink': st.st_nlink,
            'ino': st.st_ino, 'blocks': st.st_blocks, \
            'blocksize': st.st_blksize, 'ctime': st.st_ctime, 'atime': st.st_atime, 'mtime': st.st_mtime,
            'mode': st.st_mode, 'rdev': st.st_rdev, 'filename': filename, 'pmtime': time.ctime(int(st.st_mtime))}

    print "%(permission)s %(nlink)3s %(uid)5s %(gid)5s %(size)10s  %(pmtime)s  %(filename)s" % args


# Some generators
def itergen(rest, charset):
    output = []
    if rest == 0:
        return string.join(charset[0], '')
    while rest > 0:
        output.append(charset[rest % len(charset)])
        rest = rest / len(charset)
    output.reverse()
    return string.join(output, '')


class ChainedGenerator:
    def __init__(self, parent=None):
        self.parent = parent

    def __iter__(self):
        return self

    def gen_next(self):
        raise Exception("override me")

    def gen_reset(self):
        raise Exception("override me")

    def next(self):
        try:
            self.gen_next()
        except StopIteration:
            if self.parent:
                self.parent.next()
                self.gen_reset()
            else:
                raise StopIteration()
        return string.join(self.get_chain(), "")

    def get_chain(self):
        output = []
        if self.parent:
            output.extend(self.parent.get_chain())
        output.append(self.current)
        return output


class ChainedListGen(ChainedGenerator):
    def __init__(self, parent, l):
        self.list = l
        self.curiter = None
        self.gen_reset()
        self.current = ''
        ChainedGenerator.__init__(self, parent)

    def gen_reset(self):
        self.curiter = iter(self.list)

    def gen_next(self):
        self.current = self.curiter.next()


class ChainedWordlistGen(ChainedGenerator):
    def __init__(self, parent, wordfile):
        self.wordfile = wordfile
        self.fobj = None
        self.gen_reset()
        self.current = ""
        ChainedGenerator.__init__(self, parent)

    def gen_reset(self):
        if self.fobj: self.fobj.close()
        self.fobj = open(self.wordfile, "r")

    def gen_next(self):
        line = self.fobj.readline()
        if line == '': raise StopIteration()
        self.current = line.strip()


class ChainedIterGen(ChainedGenerator):
    def __init__(self, parent, charset, pos, maxvalue=None):
        self.charset = charset
        self.pos = pos
        self.maxvalue = maxvalue
        self.current = ""
        ChainedGenerator.__init__(self, parent)

    def gen_next(self):
        self.current = itergen(self.pos, self.charset)
        self.pos += 1
        if self.pos > pow(len(self.charset), self.maxvalue):
            raise StopIteration()

    def gen_reset(self):
        self.pos = 0


def usage():
    print "statls v.0.1"
    print "usage: statls -w [--wordlist=<path to wordlist>]"
    print "              -f [  --format=bew...], format of generator chain"
    print "                                        b is for bruteforce"
    print "                                        e is for extention (.tar,.zip...)"
    print "                                        w is for wordlist"
    print " example formats:"
    print "   --format=bbbbbb	# this will start bruteforcing filenames up to 6 in length"
    print "   --format=we		# this will look for common filenames with extentions"
    print "   --format=bbbe		# will look for random filenames with extentions"


def run(mastergen, basepath):
    i = 0
    for filename in mastergen:
        i += 1
        try:
            st = os.stat(basepath + "/" + filename)
            print i
            prettyreport(filename, st)
        except OSError, err:
            if err.errno == 2:
                pass
            else:
                print "Unhandled error, please tell the author!"


if __name__ == "__main__":
    # Set up options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "w:f:h", ["help", "format=", "wordlist="])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    basepath = string.join(args, ' ')
    do_wordlist_path = None
    generator_format = "bbbbbb"
    for o, a in opts:
        if o in ('-w', '--wordlist'):
            do_wordlist = True
            do_wordlist_path = a
        if o in ('-f', '--format'):
            generator_format = a
        if o in ('-h', '--help'):
            usage()
            sys.exit(0)

    # Build a generator chain
    generator_format = list(generator_format)
    generators = []
    for gentype in generator_format:
        if len(generators) == 0:
            parentgen = None
        else:
            parentgen = generators[-1]
        if gentype == "w":
            generators.append(ChainedWordlistGen(parentgen, do_wordlist_path))
        if gentype == "b":
            generators.append(ChainedIterGen(parentgen, charset_default, 0, 1))
        if gentype == "e":
            generators.append(ChainedListGen(parentgen, extentions))
    mastergen = generators[-1]

    # start searching for files/directories
    try:
        run(mastergen, basepath)
    except KeyboardInterrupt:
        print " interrupted."
        sys.exit(0)

