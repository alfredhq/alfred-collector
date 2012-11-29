import json
import msgpack
import multiprocessing
import zmq

from alfred_db.models import Push, Fix
from alfred_db.helpers import now

from markdown import markdown
from sqlalchemy import create_engine


class CollectorProcess(multiprocessing.Process):

    def __init__(self, database_uri, socket_address):
        super(CollectorProcess, self).__init__()
        self.database_uri = database_uri
        self.socket_address = socket_address

    def run(self):
        self.engine = create_engine(self.database_uri)

        context = zmq.Context()
        socket = context.socket(zmq.PULL)
        socket.bind(self.socket_address)

        while True:
            msg = socket.recv()
            self.handle_msg(msg)

        socket.close()
        context.term()

    def handle_msg(self, msg):
        push_id, msg_type, msg_data = msgpack.unpackb(msg, encoding='utf-8')

        handlers = {
            'start': self.handle_start,
            'fix': self.handle_fix,
            'finish': self.handle_finish,
        }
        handler = handlers.get(msg_type)
        if handler is not None:
            handler(push_id, msg_data)

    def handle_start(self, push_id, data):
        (Push.__table__
            .update(bind=self.engine)
            .where(Push.id==push_id)
            .execute(started_at=now()))

    def handle_fix(self, push_id, data):
        Fix.__table__.insert(bind=self.engine).execute(
            description=data['description'],
            description_html=markdown(data['description']),
            path=data['path'],
            line=data['line'],
            source=json.dumps(data['source']),
            solution=json.dumps(data['solution']),
            push_id=push_id,
        )

    def handle_finish(self, push_id, data):
        (Push.__table__
            .update(bind=self.engine)
            .where(Push.id == push_id)
            .execute(error=data, finished_at=now()))
