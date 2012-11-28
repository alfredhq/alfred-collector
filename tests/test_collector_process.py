import mock
import msgpack

from alfred_collector.process import CollectorProcess
from alfred_db import Session
from alfred_db.models import Base, Repository, Push

from sqlalchemy import create_engine
from unittest import TestCase


engine = create_engine('sqlite:///:memory:')
Session.configure(bind=engine)


def create_push():
    push = Push(
        ref='refs/heads/master',
        compare_url='https://github.com/xobb1t/test/compare/a90ff8353403...2e7be8838254',
        commit_hash='2e7be88382545a9dc7a05b9d2e85a7041e311075',
        commit_message='Update README.md',
        committer_name='Dima Kukushkin',
        committer_email='dima@kukushkin.me',
    )

    repository = Repository(
        url='https://github.com/alfredhq/alfred',
        github_id='12345',
        name='alfred',
        token='11111',
        owner_name='alfredhq',
        owner_type='organization',
        owner_id='54321',
    )
    repository.pushes.append(push)

    session = Session()
    session.add(repository)
    session.commit()
    try:
        return push.id
    finally:
        session.close()


class CollectorProcessTests(TestCase):

    def setUp(self):
        Base.metadata.create_all(engine)
        self.session = Session()

        self.process = CollectorProcess('', '')
        self.process.engine = engine

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(engine)

    def test_finishes_push(self):
        push_id = create_push()
        self.process.handle_finish(push_id, None)

        push = self.session.query(Push).get(push_id)
        self.assertIsNone(push.error)
        self.assertIsNotNone(push.finished_at)

    def test_finishes_push_with_error(self):
        push_id = create_push()
        self.process.handle_finish(push_id, 'error')

        push = self.session.query(Push).get(push_id)
        self.assertEqual(push.error, 'error')
        self.assertIsNotNone(push.finished_at)

    def test_adds_fix_to_push(self):
        push_id = create_push()
        self.process.handle_fix(push_id, {
            'description': 'description',
            'path': 'path/to/file.py',
            'line': 100,
            'source': (1, True, 'source'),
            'solution': (1, True, 'solution'),
        })

        push = self.session.query(Push).get(push_id)
        self.assertEqual(len(push.fixes.all()), 1)

        fix = push.fixes.first()
        self.assertEqual(fix.description, 'description')
        self.assertEqual(fix.description_html, '<p>description</p>')
        self.assertEqual(fix.path, 'path/to/file.py')
        self.assertEqual(fix.line, 100)
        self.assertEqual(fix.source, '[1, true, "source"]')
        self.assertEqual(fix.solution, '[1, true, "solution"]')

    @mock.patch('alfred_collector.process.CollectorProcess.handle_fix')
    @mock.patch('alfred_collector.process.CollectorProcess.handle_finish')
    def test_handles_message(self, handle_finish, handle_fix):
        self.process.handle_msg(msgpack.packb([1, 'fix', {}]))
        handle_fix.assert_called_once_with(1, {})

        self.process.handle_msg(msgpack.packb([1, 'finish', 'error']))
        handle_finish.assert_called_once_with(1, 'error')
