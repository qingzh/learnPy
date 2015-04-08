import sys
from mock import patch, MagicMock
from StringIO import StringIO

class classA:
	def get_value(cls, x):
		return len(str(x))

def fooCallable(x):
	ret = classA().get_value(x)
	print 'ClassA().get_value(): %s' % ret
	print '{}{}'.format(x, '>10' if ret >10 else '<=10')

def fooNoncallable(x):
	ret = classA.get_value(x)
	print 'ClassA.get_value(): %s' % ret 
	print '{}{}'.format(x, '>10' if ret >10 else '<=10')

def foo2(x):
	print '{}{}'.format(x, '>10' if x >10 else '<=10')

#@patch('__main__.classA', spec=['get_value'])
@patch('__main__.classA', spec=['get_value'], new_callable=MagicMock)
def test_callable_foo(mock_a):
	mock_a.get_value.return_value = 13
	mock_a.return_value.get_value.return_value = 3
	fooNoncallable('fooNoncallable')
	fooCallable('fooCallable')
	return mock_a
	#assert mock_stdout.getvalue() == '13>10'

if __name__ == '__main__':
	ret = test_callable_foo()