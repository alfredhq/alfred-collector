import mock
import msgpack

from alfred_collector.process import CollectorProcess
from alfred_db import Session
from alfred_db.models import Base, Repository, Commit, Report

from sqlalchemy import create_engine
from unittest import TestCase


engine = create_engine('sqlite:///:memory:')
Session.configure(bind=engine)


def create_report():
    report = Report()

    commit = Commit(
        hash='2e7be88382545a9dc7a05b9d2e85a7041e311075',
        ref='refs/heads/master',
        compare_url='https://github.com/xobb1t/test/compare/a90ff8353403...2e7be8838254',
        committer_name='Dima Kukushkin',
        committer_email='dima@kukushkin.me',
        message='Update README.md',
    )
    commit.report = report

    repository = Repository(
        url='https://github.com/alfredhq/alfred',
        name='alfred',
        user='alfredhq',
    )
    repository.commits.append(commit)

    session = Session()
    session.add(repository)
    session.commit()
    try:
        return report.id
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

    def test_finishes_report(self):
        report_id = create_report()
        self.process.handle_finish(report_id, None)

        report = self.session.query(Report).get(report_id)
        self.assertIsNone(report.error)
        self.assertIsNotNone(report.finished_on)

    def test_finishes_report_with_error(self):
        report_id = create_report()
        self.process.handle_finish(report_id, 'error')

        report = self.session.query(Report).get(report_id)
        self.assertEqual(report.error, 'error')
        self.assertIsNotNone(report.finished_on)

    def test_adds_fix_to_report(self):
        report_id = create_report()
        self.process.handle_fix(report_id, {
            'description': 'description',
            'path': 'path/to/file.py',
            'line': 100,
            'source': 'source',
            'solution': 'solution',
        })

        report = self.session.query(Report).get(report_id)
        self.assertEqual(len(report.fixes.all()), 1)

        fix = report.fixes.first()
        self.assertEqual(fix.description, 'description')
        self.assertEqual(fix.description_html, '<p>description</p>')
        self.assertEqual(fix.path, 'path/to/file.py')
        self.assertEqual(fix.line, 100)
        self.assertEqual(fix.source, 'source')
        self.assertEqual(fix.solution, 'solution')

    @mock.patch('alfred_collector.process.CollectorProcess.handle_fix')
    @mock.patch('alfred_collector.process.CollectorProcess.handle_finish')
    def test_handles_message(self, handle_finish, handle_fix):
        self.process.handle_msg(msgpack.packb([1, 'fix', {}]))
        handle_fix.assert_called_once_with(1, {})

        self.process.handle_msg(msgpack.packb([1, 'finish', 'error']))
        handle_finish.assert_called_once_with(1, 'error')
