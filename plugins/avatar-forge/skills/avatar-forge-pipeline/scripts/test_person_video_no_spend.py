"""Direct-video orchestration tests; all HTTP/auth mocked, no paid tasks."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_pipeline_no_spend import PIPELINE as p, FakeSession, FakeResponse


class DirectSession(FakeSession):
    def __init__(self):
        super().__init__()
        self.fail_poll = False
        self.unknown_clone = False

    def post(self, url, **kwargs):
        assert not url.endswith('/template'), 'RunningHub forbidden for video'
        if url.endswith('/avatar/clone'):
            self.posts.append(url)
            assert kwargs['files']['video'][1].read() == b'PERSON_VIDEO'
            assert kwargs['data'] == {}
            if self.unknown_clone:
                raise p.requests.Timeout('mock lost response')
            return FakeResponse(payload={'assetId': 'direct-asset', 'requestId': 'clone-1'})
        if url.endswith('/avatar/infer'):
            assert kwargs['data'] == {'assetId': 'direct-asset', 'playerId': 'player-1'}
        return super().post(url, **kwargs)

    def get(self, url, **kwargs):
        assert '/task/' not in url and 'internal.invalid' not in url
        if self.fail_poll:
            self.fail_poll = False
            raise p.requests.Timeout('mock poll timeout')
        return super().get(url, **kwargs)


class PersonVideoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = self.root / 'person.mp4'
        self.video.write_bytes(b'PERSON_VIDEO')
        self.audio = self.root / 'speech.mp3'
        self.audio.write_bytes(b'SPEECH')
        self.script = self.root / 'script.txt'
        self.script.write_text('这是一次不产生真实费用的流程测试。', encoding='utf-8')
        self.output = self.root / 'result.mp4'
        self.session = DirectSession()

    def run_flow(self, full=False):
        args = ['run_pipeline.py', '--video', str(self.video), '--output', str(self.output), '--poll-seconds', '0']
        args += ['--speaker-id', 'speaker-1', '--script-file', str(self.script)] if full else ['--avatar-only', '--audio', str(self.audio)]
        with patch.object(sys, 'argv', args), patch.object(p, 'authorized_session', return_value=self.session), patch.object(p, 'validate_video_input'), patch.object(p, 'FIXED_TEMPLATE_DRIVER', self.root / 'absent.wav'):
            return p.main()

    def test_existing_audio_resume_and_source_preserved(self):
        self.assertEqual(self.run_flow(), 0)
        self.assertEqual(len(self.session.posts), 2)
        self.run_flow()
        self.assertEqual(len(self.session.posts), 2)
        self.assertEqual(self.output.read_bytes(), b'ZEROSHOT_FINAL_ONLY')
        self.assertEqual(self.video.read_bytes(), b'PERSON_VIDEO')
        state = json.loads((self.root / '.avatar-forge/result/state.json').read_text())
        self.assertEqual(state['flow'][0], 'person-video')
        self.assertNotIn('templateTaskId', state)
        self.video.write_bytes(b'CHANGED')
        with self.assertRaisesRegex(p.PipelineError, 'different inputs'):
            self.run_flow()

    def test_script_with_speaker(self):
        self.run_flow(full=True)
        self.assertEqual([u.rsplit('/', 1)[1] for u in self.session.posts], ['file', 'clone', 'infer'])
        self.run_flow(full=True)
        self.assertEqual(len(self.session.posts), 3)

    def test_poll_timeout_resumes_clone(self):
        self.session.fail_poll = True
        with self.assertRaises(p.requests.Timeout):
            self.run_flow()
        self.run_flow()
        self.assertEqual(len(self.session.posts), 2)

    def test_unknown_submission_is_not_retried(self):
        self.session.unknown_clone = True
        with self.assertRaises(p.requests.Timeout):
            self.run_flow()
        with self.assertRaisesRegex(p.PipelineError, 'outcome is unknown'):
            self.run_flow()
        self.assertEqual(len(self.session.posts), 1)

    def test_mutually_exclusive_inputs(self):
        with patch.object(sys, 'argv', ['run_pipeline.py', '--image', 'a.png', '--video', 'b.mp4']), self.assertRaises(SystemExit):
            p.parse_args()

    def test_probe_requires_real_video(self):
        for media in ({'format': {'duration': '1'}, 'streams': []}, {'format': {'duration': 'nan'}, 'streams': [{'codec_type': 'video'}]}):
            with patch.object(p.subprocess, 'run') as run:
                run.return_value.stdout = json.dumps(media)
                with self.assertRaises(p.PipelineError):
                    p.validate_video_input(self.video)
        with patch.object(p.subprocess, 'run') as run:
            run.return_value.stdout = json.dumps({'format': {'duration': '120'}, 'streams': [{'codec_type': 'video', 'width': 1080, 'height': 1920, 'avg_frame_rate': '25/1', 'r_frame_rate': '25/1'}]})
            p.validate_video_input(self.video)

    def test_metadata_limits(self):
        for override in ({'width': 1921}, {'height': 1081}, {'avg_frame_rate': '30/1'}, {'r_frame_rate': '50/1'}, {'avg_frame_rate': '0/0'}):
            stream = dict(codec_type='video', width=1920, height=1080, avg_frame_rate='25/1', r_frame_rate='25/1')
            stream.update(override)
            with patch.object(p.subprocess, 'run') as run:
                run.return_value.stdout = json.dumps({'format': {'duration': '120'}, 'streams': [stream]})
                with self.assertRaises(p.PipelineError):
                    p.validate_video_input(self.video)
        with patch.object(p.subprocess, 'run') as run:
            run.return_value.stdout = json.dumps({'format': {'duration': '120.001'}, 'streams': [{'codec_type': 'video'}]})
            with self.assertRaisesRegex(p.PipelineError, '2分钟'):
                p.validate_video_input(self.video)


if __name__ == '__main__':
    unittest.main()
