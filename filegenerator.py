from Queue import Queue
from time import sleep
import threading


class FileGenerator(object):
    def __init__(self):
        self.q = Queue()

    def read_generator(self):
        running = True
        while(running):
            try:
                data = self.q.get(block=True, timeout=1)
                self.q.task_done()
                if data is None:
                    running = False
                else:
                    yield data
            except:
                running = False

    def write(self, s):
        self.q.put(s)

    def close(self):
        self.q.put(None)

    def tell(self):
        return 0

    def flush(self):
        return True


class GeneratorWorker(threading.Thread):
    def __init__(self, generator):
        self.__generator = generator
        threading.Thread.__init__(self)

    def run(self):
        for x in self.__generator:
            print 'got: ', x

if __name__ == '__main__':
    f = FileGenerator()

    GeneratorWorker(f.read_generator()).start()

    f.write('Test')
    sleep(1)
    f.write('ing')
    f.close()
