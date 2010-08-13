import httplib
import collections
import threading
import pygame
from StringIO import StringIO
from pymt import *
from OpenGL.GL import GL_RGBA, GL_RGB

class MJpegClientException(Exception):
    pass

class MJpegClient(EventDispatcher):
    '''Client for mjpeg stream, designed for Movid.

    :Parameters:
        `host`: string, default to '127.0.0.1'
            Movid hostname to connect
        `port`: int, default to 7500
            Movid default port
        `objectname`: string, default to None
            Object to get the stream
        `scale`: int, default to 2
            Inverse scale of the image. (2 mean size will be divided by 2)

    :Events:
        `on_image` (width, height, mode, data)
            Fired when we receive a new image. Ideal to create a texture and
            blit data on the texture !
        `on_exception` (exception):
            Fired when an exception append in the thread. By default, the
            exception is raised in the main thread.
    '''
    def __init__(self, **kwargs):
        super(MJpegClient, self).__init__()

        self.register_event_type('on_image')
        self.register_event_type('on_exception')

        self.daemon = True
        self.host = kwargs.get('host', '127.0.0.1')
        self.port = kwargs.get('port', 7500)
        self.objectname = kwargs.get('objectname', None)
        self.scale = 2
        self.timeout = 10
        self.queue = collections.deque()

        self._state = 'boundary'
        self._boundary = None
        self._wantquit = False

        if not self.objectname:
            raise AttributeError('objectname argument missing')

        self.thread = threading.Thread(target=self._thread_run_exit)
        self.thread.daemon = True

    def _thread_run_exit(self):
        try:
            self._thread_run()
        except Exception, e:
            self.queue.appendleft(e)

    def _thread_run(self):
        # make the connection to movid
        conn = httplib.HTTPConnection(
            self.host, self.port, timeout=self.timeout)
        conn.request('GET', '/pipeline/stream?objectname=%s&scale=%d' % (
                     self.objectname, self.scale))
        resp = conn.getresponse()

        # ensure it's a stream
        header = resp.getheader('Content-Type', None)
        if header is None or not header.startswith('multipart/x-mixed-replace; boundary='):
            raise MJpegClientException('Invalid request (object not found ?)')

        # parse response
        self._thread_parse_response(resp)

    def _thread_parse_response(self, resp):
        self._boundary = '--%s' % resp.getheader('Content-Type').split('boundary=')[1]
        queue = self.queue
        while not self._wantquit:

            # first part, search headers
            data = ''
            while data[-4:] != '\r\n\r\n':
                data += resp.read(1)
            headers = self._thread_parse_headers(data)

            # ensure that the headers have a valid content-length
            length = int(headers.get('Content-Length', 0))
            if length <= 0:
                raise MJpegClientException('Invalid content length in headers')

            # read data
            data = resp.read(length)

            # convert data to an image (we assume it's a jpeg.. since we are in
            # MJpegStream module !)
            fd = StringIO(data)
            im = pygame.image.load(fd, 'test.jpg')
            if im.get_bytesize() < 3:
                im = surface.convert(32)
            if im.get_bytesize() == 3:
                mode = 'RGB'
            else:
                mode = 'RGBA'
            data = pygame.image.tostring(im, mode, True)
            
            # push the image on the queue
            queue.appendleft((im.get_width(), im.get_height(), mode, data))


    def _thread_parse_headers(self, data):
        lines = data.split('\r\n')
        if len(lines) == 0:
            raise MJpegClientException('No headers found in data')
        if lines[0] != self._boundary:
            raise MJpegClientException('Invalid boundary in headers')
        headers = dict()
        for line in lines[1:]:
            if not ':' in line:
                continue
            key, value = [x.strip() for x in line.split(':')]
            headers[key] = value
        return headers

    def start(self):
        self._wantquit = False
        self.thread.start()

    def stop(self):
        self._wantquit = True

    def loop(self):
        while True:
            self.update()

    def update(self):
        while True:
            try:
                data = self.queue.pop()
            except IndexError:
                return
            if isinstance(data, Exception):
                self.stop()
                self.dispatch_event('on_exception', data)
                return
            self.dispatch_event('on_image', *data)

    def on_image(self, width, height, mode, data):
        pass

    def on_exception(self, exc):
        raise exc

class MTMJpegClient(MTScatterWidget):
    def __init__(self, client, **kwargs):
        super(MTMJpegClient, self).__init__(**kwargs)
        self.client = client
        self.client.connect('on_image', self.on_image)
        self.texture = None

    def on_image(self, width, height, mode, data):
        if self.texture is None or self.texture.size != (width, height):
            self.texture = Texture.create(width, height, GL_RGB)
        self.texture.blit_buffer(data, mode=mode)

    def on_update(self):
        super(MTMJpegClient, self).on_update()
        self.client.update()
        if self.texture:
            self.size = self.texture.size

    def draw(self):
        if self.texture:
            set_color(1, 1, 1)
            drawTexturedRectangle(texture=self.texture, size=self.texture.size)

if __name__ == '__main__':
    # Usage within a scatter widget
    client = MJpegClient(objectname='cam')
    client.start()
    runTouchApp(MTMJpegClient(client))

    '''
    # Standalone usage
    m = MJpegClient(objectname='cam')
    m.start()
    m.loop()
    '''

