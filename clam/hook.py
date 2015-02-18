import collections
import os
from clam import logger

hooks = collections.defaultdict(list)


def register(event_name, func):
	logger.info('Registered "%s" for event "%s:%s"', event_name, func.__name__, func.func_code.co_filename.split(os.sep)[-1])
	hooks[event_name].append(func)


def call(event_name, req, *args):
	retdata = []
	for x in hooks[event_name]:
		logger.debug('Dispatched "%s" to "%s:%s" with args %s', event_name, x.__name__, x.func_code.co_filename.split(os.sep)[-1], str(args))
		try:
			retdata.append(x(req, *args))
		except Exception as e:
			logger.critical(e)
	return retdata 