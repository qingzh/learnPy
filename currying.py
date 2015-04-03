#! -*- coding: utf-8 -*-

class currying:
	@staticmethod
	def inc(x):
		def incx(y):
			return x+y
		return incx

inc2 = currying.inc(2)
inc5 = currying.inc(5)
