import msgpack
import multiprocessing
import zmq
from datetime import datetime
from markdown import markdown
from sqlalchemy import create_engine

from alfred_db import Session
from alfred_db.models import Commit, Report, Fix


class CollectorProcess(multiprocessing.Process):

    def __init__(self, database_uri, socket_address):
        super().__init__()
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
        report_id, msg_type, msg_data = msgpack.unpackb(msg, encoding='utf-8')

        handlers = {
            'fix': self.handle_fix,
            'finish': self.handle_finish,
        }
        handler = handlers.get(msg_type)
        if handler is not None:
            handler(report_id, msg_data)

    def handle_fix(self, report_id, data):
        Fix.__table__.insert(bind=self.engine).execute(
            description=data['description'],
            description_html=markdown(data['description']),
            path=data['path'],
            line=data['line'],
            source=data['source'],
            solution=data['solution'],
            report_id=report_id,
        )

    def handle_finish(self, report_id, data):
        (Report.__table__
            .update(bind=self.engine)
            .where(Report.id==report_id)
            .execute(error=data, finished_on=datetime.utcnow()))
