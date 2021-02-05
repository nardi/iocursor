# coding: utf-8

# adapted from the Python tests for the builtin `io` module:
# https://github.com/python/cpython/blob/master/Lib/test/test_memoryio.py

import array
import io
import pickle
import sys
import unittest

import iocursor


class IntLike:
    def __init__(self, num):
        self._num = num
    def __index__(self):
        return self._num
    __int__ = __index__


class MemorySeekTestMixin:

    def test_init(self):
        buf = self.buftype("1234567890")
        cursor = self.ioclass(buf)

    def test_read_simple(self):
        buf = self.buftype("1234567890")
        cursor = self.ioclass(buf)

        self.assertEqual(buf[:1], cursor.read(1))
        self.assertEqual(buf[1:5], cursor.read(4))
        self.assertEqual(buf[5:], cursor.read(900))
        self.assertEqual(self.EOF, cursor.read())

        buf = self.buftype("1234567890")
        cursor = self.ioclass(buf)

        self.assertEqual(buf, cursor.read())
        self.assertEqual(self.EOF, cursor.read())

    def test_seek_simple(self):
        buf = self.buftype("1234567890")
        cursor = self.ioclass(buf)

        self.assertEqual(cursor.read(5), buf[:5])
        self.assertEqual(cursor.seek(0), 0)
        self.assertEqual(buf, cursor.read())

        self.assertEqual(cursor.seek(3), 3)
        self.assertEqual(buf[3:], cursor.read())
        self.assertRaises(TypeError, cursor.seek, 0.0)


class MemoryTestMixin:

    def test_detach(self):
        buf = self.ioclass(b"")
        self.assertRaises(io.UnsupportedOperation, buf.detach)

    def write_ops(self, f, t):
        self.assertEqual(f.write(t("blah.")), 5)
        self.assertEqual(f.seek(0), 0)
        self.assertEqual(f.write(t("Hello.")), 6)
        self.assertEqual(f.tell(), 6)
        self.assertEqual(f.seek(5), 5)
        self.assertEqual(f.tell(), 5)
        self.assertEqual(f.write(t(" world\n\n\n")), 9)
        self.assertEqual(f.seek(0), 0)
        self.assertEqual(f.write(t("h")), 1)
        # NOTE: `truncate` is not supported
        # self.assertEqual(f.truncate(12), 12)
        self.assertEqual(f.tell(), 1)

    def test_relative_seek(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        self.assertEqual(memio.seek(-1, 1), 0)
        self.assertEqual(memio.seek(3, 1), 3)
        self.assertEqual(memio.seek(-4, 1), 0)
        self.assertEqual(memio.seek(-1, 2), 9)
        self.assertEqual(memio.seek(1, 1), 10)
        self.assertEqual(memio.seek(1, 2), 11)
        memio.seek(-3, 2)
        self.assertEqual(memio.read(), buf[-3:])
        memio.seek(0)
        memio.seek(1, 1)
        self.assertEqual(memio.read(), buf[1:])

    def test_unicode(self):
        memio = self.ioclass(self.buftype(""))

        self.assertRaises(TypeError, self.ioclass, "1234567890")
        self.assertRaises(TypeError, memio.write, "1234567890")

        if not memio.readonly:
            self.assertRaises(TypeError, memio.writelines, ["1234567890"])

    def test_truncate(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        # NOTE: truncate is unsupported
        # self.assertRaises(ValueError, memio.truncate, -1)
        # self.assertRaises(ValueError, memio.truncate, IntLike(-1))
        # memio.seek(6)
        # self.assertEqual(memio.truncate(IntLike(8)), 8)
        # self.assertEqual(memio.getvalue(), buf[:8])
        # self.assertEqual(memio.truncate(), 6)
        # self.assertEqual(memio.getvalue(), buf[:6])
        # self.assertEqual(memio.truncate(4), 4)
        # self.assertEqual(memio.getvalue(), buf[:4])
        # self.assertEqual(memio.tell(), 6)
        # memio.seek(0, 2)
        # memio.write(buf)
        # self.assertEqual(memio.getvalue(), buf[:4] + buf)
        # pos = memio.tell()
        # self.assertEqual(memio.truncate(None), pos)
        # self.assertEqual(memio.tell(), pos)
        self.assertRaises(io.UnsupportedOperation, memio.truncate)
        self.assertRaises(TypeError, memio.truncate, '0')
        memio.close()
        self.assertRaises(ValueError, memio.truncate, 0)
        self.assertRaises(ValueError, memio.truncate, IntLike(0))

    def test_init(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)
        self.assertEqual(memio.getvalue(), buf)
        memio.__init__(buf * 2)
        self.assertEqual(memio.getvalue(), buf * 2)
        memio.__init__(buf)
        self.assertEqual(memio.getvalue(), buf)
        self.assertRaises(TypeError, memio.__init__, [])

    def test_read(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        self.assertEqual(memio.read(0), self.EOF)
        self.assertEqual(memio.read(1), buf[:1])
        self.assertEqual(memio.read(4), buf[1:5])
        self.assertEqual(memio.read(900), buf[5:])
        self.assertEqual(memio.read(), self.EOF)
        memio.seek(0)
        self.assertEqual(memio.read(IntLike(0)), self.EOF)
        self.assertEqual(memio.read(IntLike(1)), buf[:1])
        self.assertEqual(memio.read(IntLike(4)), buf[1:5])
        self.assertEqual(memio.read(IntLike(900)), buf[5:])
        memio.seek(0)
        self.assertEqual(memio.read(), buf)
        self.assertEqual(memio.read(), self.EOF)
        self.assertEqual(memio.tell(), 10)
        memio.seek(0)
        self.assertEqual(memio.read(-1), buf)
        memio.seek(0)
        self.assertEqual(memio.read(IntLike(-1)), buf)
        memio.seek(0)
        self.assertEqual(type(memio.read()), bytes)
        memio.seek(100)
        self.assertEqual(type(memio.read()), bytes)
        memio.seek(0)
        self.assertEqual(memio.read(None), buf)
        self.assertRaises(TypeError, memio.read, '')
        memio.seek(len(buf) + 1)
        self.assertEqual(memio.read(1), self.EOF)
        memio.seek(len(buf) + 1)
        self.assertEqual(memio.read(IntLike(1)), self.EOF)
        memio.seek(len(buf) + 1)
        self.assertEqual(memio.read(), self.EOF)
        memio.close()
        self.assertRaises(ValueError, memio.read)

    def test_readline(self):
        buf = self.buftype("1234567890\n")
        memio = self.ioclass(buf * 2)

        self.assertEqual(memio.readline(0), self.EOF)
        self.assertEqual(memio.tell(), 0)
        self.assertEqual(memio.readline(IntLike(0)), self.EOF)
        self.assertEqual(memio.tell(), 0)
        self.assertEqual(memio.readline(), buf)
        self.assertEqual(memio.tell(), 11)
        self.assertEqual(memio.readline(), buf)
        self.assertEqual(memio.readline(), self.EOF)
        self.assertEqual(memio.seek(0), 0)
        self.assertEqual(memio.readline(5), buf[:5])
        self.assertEqual(memio.tell(), 5)
        self.assertEqual(memio.readline(5), buf[5:10])
        self.assertEqual(memio.readline(5), buf[10:15])
        self.assertEqual(memio.seek(0), 0)
        self.assertEqual(memio.readline(IntLike(5)), buf[:5])
        self.assertEqual(memio.readline(IntLike(5)), buf[5:10])
        self.assertEqual(memio.readline(IntLike(5)), buf[10:15])
        self.assertEqual(memio.seek(0), 0)
        self.assertEqual(memio.readline(-1), buf)
        self.assertEqual(memio.seek(0), 0)
        self.assertEqual(memio.readline(IntLike(-1)), buf)
        self.assertEqual(memio.seek(0), 0)
        self.assertEqual(memio.readline(0), self.EOF)
        self.assertEqual(memio.readline(IntLike(0)), self.EOF)
        # Issue #24989: Buffer overread
        memio.seek(len(buf) * 2 + 1)
        self.assertEqual(memio.readline(), self.EOF)

        buf = self.buftype("1234567890\n")
        memio = self.ioclass((buf * 3)[:-1])
        self.assertEqual(memio.readline(), buf)
        self.assertEqual(memio.readline(), buf)
        self.assertEqual(memio.readline(), buf[:-1])
        self.assertEqual(memio.readline(), self.EOF)
        memio.seek(0)
        self.assertEqual(type(memio.readline()), bytes)
        self.assertEqual(memio.readline(), buf)
        self.assertRaises(TypeError, memio.readline, '')
        memio.close()
        self.assertRaises(ValueError,  memio.readline)

    def test_readlines(self):
        buf = self.buftype("1234567890\n")
        memio = self.ioclass(buf * 10)

        self.assertEqual(memio.readlines(), [buf] * 10)
        memio.seek(5)
        self.assertEqual(memio.readlines(), [buf[5:]] + [buf] * 9)
        memio.seek(0)
        self.assertEqual(memio.readlines(15), [buf] * 2)
        memio.seek(0)
        self.assertEqual(memio.readlines(-1), [buf] * 10)
        memio.seek(0)
        self.assertEqual(memio.readlines(0), [buf] * 10)
        memio.seek(0)
        self.assertEqual(type(memio.readlines()[0]), bytes)
        memio.seek(0)
        self.assertEqual(memio.readlines(None), [buf] * 10)
        self.assertRaises(TypeError, memio.readlines, '')
        # Issue #24989: Buffer overread
        memio.seek(len(buf) * 10 + 1)
        self.assertEqual(memio.readlines(), [])
        memio.close()
        self.assertRaises(ValueError, memio.readlines)

    def test_iterator(self):
        buf = self.buftype("1234567890\n")
        memio = self.ioclass(buf * 10)

        self.assertEqual(iter(memio), memio)
        self.assertTrue(hasattr(memio, '__iter__'))
        self.assertTrue(hasattr(memio, '__next__'))
        i = 0
        for line in memio:
            self.assertEqual(line, buf)
            i += 1
        self.assertEqual(i, 10)
        memio.seek(0)
        i = 0
        for line in memio:
            self.assertEqual(line, buf)
            i += 1
        self.assertEqual(i, 10)
        # Issue #24989: Buffer overread
        memio.seek(len(buf) * 10 + 1)
        self.assertEqual(list(memio), [])
        memio = self.ioclass(buf * 2)
        memio.close()
        self.assertRaises(ValueError, memio.__next__)

    def test_getvalue(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        self.assertEqual(memio.getvalue(), buf)
        memio.read()
        self.assertEqual(memio.getvalue(), buf)
        self.assertEqual(type(memio.getvalue()), type(buf))
        memio = self.ioclass(buf * 1000)
        self.assertEqual(memio.getvalue()[-3:], self.buftype("890"))
        memio = self.ioclass(buf)
        memio.close()
        self.assertRaises(ValueError, memio.getvalue)

    def test_seek(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        memio.read(5)
        self.assertRaises(ValueError, memio.seek, -1)
        self.assertRaises(ValueError, memio.seek, 1, -1)
        self.assertRaises(ValueError, memio.seek, 1, 3)
        self.assertEqual(memio.seek(0), 0)
        self.assertEqual(memio.seek(0, 0), 0)
        self.assertEqual(memio.read(), buf)
        self.assertEqual(memio.seek(3), 3)
        self.assertEqual(memio.seek(0, 1), 3)
        self.assertEqual(memio.read(), buf[3:])
        self.assertEqual(memio.seek(len(buf)), len(buf))
        self.assertEqual(memio.read(), self.EOF)
        memio.seek(len(buf) + 1)
        self.assertEqual(memio.read(), self.EOF)
        self.assertEqual(memio.seek(0, 2), len(buf))
        self.assertEqual(memio.read(), self.EOF)
        memio.close()
        self.assertRaises(ValueError, memio.seek, 0)

    def test_overseek(self):
       buf = self.buftype("1234567890")
       memio = self.ioclass(buf)

       self.assertEqual(memio.seek(len(buf) + 1), 11)
       self.assertEqual(memio.read(), self.EOF)
       self.assertEqual(memio.tell(), 11)
       self.assertEqual(memio.getvalue(), buf)

       if not memio.readonly:
           memio.write(self.EOF)
           self.assertEqual(memio.getvalue(), buf)
           # memio.write(buf)
           # self.assertEqual(memio.getvalue(), buf + self.buftype('\0') + buf)

    def test_tell(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        self.assertEqual(memio.tell(), 0)
        memio.seek(5)
        self.assertEqual(memio.tell(), 5)
        memio.seek(10000)
        self.assertEqual(memio.tell(), 10000)
        memio.close()
        self.assertRaises(ValueError, memio.tell)

    def test_flush(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        self.assertEqual(memio.flush(), None)

    def test_flags_closed(self):
        buf = self.buftype("abc")
        memio = self.ioclass(buf)

        memio.close()
        self.assertRaises(ValueError, memio.writable)
        self.assertRaises(ValueError, memio.readable)
        self.assertRaises(ValueError, memio.seekable)
        self.assertRaises(ValueError, memio.isatty)
        self.assertEqual(memio.closed, True)

    def test_subclassing(self):
        buf = self.buftype("1234567890")
        def test1():
            class MemIO(self.ioclass):
                pass
            m = MemIO(buf)
            return m.getvalue()
        def test2():
            class MemIO(self.ioclass):
                def __init__(me, a, b):
                    self.ioclass.__init__(me, a)
            m = MemIO(buf, None)
            return m.getvalue()
        self.assertEqual(test1(), buf)
        self.assertEqual(test2(), buf)

    def test_read1(self):
        buf = self.buftype("1234567890")
        self.assertEqual(self.ioclass(buf).read1(), buf)
        self.assertEqual(self.ioclass(buf).read1(-1), buf)

    def test_readinto(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)

        b = bytearray(b"hello")
        self.assertEqual(memio.readinto(b), 5)
        self.assertEqual(b, b"12345")
        self.assertEqual(memio.readinto(b), 5)
        self.assertEqual(b, b"67890")
        self.assertEqual(memio.readinto(b), 0)
        self.assertEqual(b, b"67890")
        b = bytearray(b"hello world")
        memio.seek(0)
        self.assertEqual(memio.readinto(b), 10)
        self.assertEqual(b, b"1234567890d")
        b = bytearray(b"")
        memio.seek(0)
        self.assertEqual(memio.readinto(b), 0)
        self.assertEqual(b, b"")
        self.assertRaises(TypeError, memio.readinto, '')
        import array
        a = array.array('b', b"hello world")
        memio = self.ioclass(buf)
        memio.readinto(a)
        self.assertEqual(a.tobytes(), b"1234567890d")
        memio.close()
        self.assertRaises(ValueError, memio.readinto, b)
        memio = self.ioclass(b"123")
        b = bytearray()
        memio.seek(42)
        memio.readinto(b)
        self.assertEqual(b, b"")

    def test_issue5449(self):
        buf = self.buftype("1234567890")
        self.ioclass(buffer=buf)
        self.assertRaises(TypeError, self.ioclass, buf, foo=None)

    def test_flags(self):
        buf = self.buftype("abcd")
        cursor = self.ioclass(buf)

        self.assertEqual(cursor.writable(), not cursor.readonly)
        self.assertEqual(cursor.readable(), True)
        self.assertEqual(cursor.seekable(), True)
        self.assertEqual(cursor.isatty(), False)
        self.assertEqual(cursor.closed, False)

    @unittest.expectedFailure
    def test_instance_dict_leak(self):
        # Test case for issue #6242.
        # This will be caught by regrtest.py -R if this leak.
        for _ in range(100):
            memio = self.ioclass()
            memio.foo = 1

    @unittest.expectedFailure
    def test_pickling(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(buf)
        memio.foo = 42
        memio.seek(2)

        class PickleTestMemIO(self.ioclass):
            def __init__(me, initvalue, foo):
                self.ioclass.__init__(me, initvalue)
                me.foo = foo
            # __getnewargs__ is undefined on purpose. This checks that PEP 307
            # is used to provide pickling support.

        # Pickle expects the class to be on the module level. Here we use a
        # little hack to allow the PickleTestMemIO class to derive from
        # self.ioclass without having to define all combinations explicitly on
        # the module-level.
        import __main__
        PickleTestMemIO.__module__ = '__main__'
        PickleTestMemIO.__qualname__ = PickleTestMemIO.__name__
        __main__.PickleTestMemIO = PickleTestMemIO
        submemio = PickleTestMemIO(buf, 80)
        submemio.seek(2)

        # We only support pickle protocol 2 and onward since we use extended
        # __reduce__ API of PEP 307 to provide pickling support.
        for proto in range(2, pickle.HIGHEST_PROTOCOL + 1):
            for obj in (memio, submemio):
                obj2 = pickle.loads(pickle.dumps(obj, protocol=proto))
                self.assertEqual(obj.getvalue(), obj2.getvalue())
                self.assertEqual(obj.__class__, obj2.__class__)
                self.assertEqual(obj.foo, obj2.foo)
                self.assertEqual(obj.tell(), obj2.tell())
                obj2.close()
                self.assertRaises(ValueError, pickle.dumps, obj2, proto)
        del __main__.PickleTestMemIO

    def test_bytes_array(self):
        buf = b"1234567890"
        a = array.array('b', list(buf))
        memio = self.ioclass(a)
        self.assertEqual(memio.getvalue().tobytes(), buf)
        self.assertEqual(memio.write(a[::-1]), 10)
        self.assertEqual(memio.getvalue().tobytes(), buf[::-1])

class CursorBytearrayTest(MemoryTestMixin, MemorySeekTestMixin, unittest.TestCase):

    @staticmethod
    def buftype(s):
        return bytearray(s.encode("ascii"))

    ioclass = iocursor.Cursor
    EOF = b""

    def test_write(self):
        buf = self.buftype("hello world\n\0\0\0\0\0\0\0\0\0\0")
        memio = self.ioclass(buf)

        self.write_ops(memio, self.buftype)
        self.assertEqual(memio.getvalue(), buf)
        self.assertRaises(TypeError, memio.write, None)
        memio.close()
        self.assertRaises(ValueError, memio.write, self.buftype(""))

        # memio = self.ioclass(b"")
        # self.write_ops(memio, self.buftype)
        # self.assertEqual(memio.getvalue(), buf)

    def test_writelines(self):
        buf = self.buftype("1234567890")
        memio = self.ioclass(bytearray(10 * 100))

        self.assertEqual(memio.writelines([buf] * 100), None)
        self.assertEqual(memio.getvalue(), buf * 100)
        memio.writelines([])
        self.assertEqual(memio.getvalue(), buf * 100)

        memio = self.ioclass(bytearray(10))
        self.assertRaises(TypeError, memio.writelines, [buf] + [1])
        self.assertEqual(memio.getvalue(), buf)
        self.assertRaises(TypeError, memio.writelines, None)
        memio.close()
        self.assertRaises(ValueError, memio.writelines, [])

    def test_writelines_error(self):
        memio = self.ioclass(bytearray(10))
        def error_gen():
            yield self.buftype('spam')
            raise KeyboardInterrupt

        self.assertRaises(KeyboardInterrupt, memio.writelines, error_gen())


class CursorBytesTest(MemoryTestMixin, MemorySeekTestMixin, unittest.TestCase):

    @staticmethod
    def buftype(s):
        return s.encode("ascii")

    ioclass = iocursor.Cursor
    EOF = b""

    @unittest.expectedFailure
    def test_getbuffer(self):
        memio = self.ioclass(b"1234567890")
        buf = memio.getbuffer()
        self.assertEqual(bytes(buf), b"1234567890")
        memio.seek(5)
        buf = memio.getbuffer()
        self.assertEqual(bytes(buf), b"1234567890")
        # Trying to change the size of the cursor while a buffer is exported
        # raises a BufferError.
        self.assertRaises(BufferError, memio.write, b'x' * 100)
        self.assertRaises(BufferError, memio.truncate)
        self.assertRaises(BufferError, memio.close)
        self.assertFalse(memio.closed)
        # Mutating the buffer updates the cursor
        buf[3:6] = b"abc"
        self.assertEqual(bytes(buf), b"123abc7890")
        self.assertEqual(memio.getvalue(), b"123abc7890")
        # After the buffer gets released, we can resize and close the cursor
        # again
        del buf
        support.gc_collect()
        memio.truncate()
        memio.close()
        self.assertRaises(ValueError, memio.getbuffer)


if __name__ == '__main__':
    unittest.main()
