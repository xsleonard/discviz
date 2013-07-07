#!/usr/bin/env python

import os
import subprocess
import shlex
import discviz
from setuptools import setup, find_packages, Command


class Test(Command):
    ''' Test discviz application with the following:
        pep8 conformance (style)
        pyflakes validation (static analysis)
        nosetests (code tests) [--with-integration] [--run-failed]
    '''
    description = 'Test Forq source code'
    user_options = [('with-integration', None,
                     'Run integration tests in addition to regular tests.'),
                    ('integration-only', None,
                     'Run only the integration tests.'),
                    ('run-failed', None,
                     'Run only the previously failed tests.'),
                    ('nose-only', None, 'Run only the nose tests.')]
    boolean_options = ['with-integration', 'run-failed', 'nose-only']

    def initialize_options(self):
        self.with_integration = False
        self.integration_only = False
        self.run_failed = False
        self.nose_only = False
        self.flake8 = 'flake8 --ignore=E712 discviz/ tests/'
        os.environ['FORQ_SETTINGS'] = '../config/test.py'

    def finalize_options(self):
        pass

    def _no_print_statements(self):
        cmd = 'grep -rnw print discviz/ config/'
        p = subprocess.Popen(shlex.split(cmd), close_fds=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = p.stderr.read().strip()
        if err:
            msg = 'ERROR: stderr not empty for print statement grep: {0}'
            print msg.format(err)
            raise SystemExit(-1)
        output = p.stdout.read().strip()
        if output:
            print 'ERROR: Found print statements in source code:'
            print output
            raise SystemExit(-1)

    def _get_py_files(self, basepath, subpath=''):
        files = []
        badchars = ['.', '_', '~']
        path = os.path.join(basepath, subpath)
        for f in os.listdir(path):
            if (not f.endswith('.py') or
                    any(map(lambda c: f.startswith(c), badchars))):
                continue
            files.append(os.path.join(subpath, f))
        return files

    def _get_nose_command(self):
        nosecmd = ('nosetests -v -w tests/ --with-coverage '
                   '--cover-package=discviz --disable-docstring')
        testfiles = []
        if self.integration_only:
            testfiles = self._get_py_files('tests/', 'integration/')
        else:
            testfiles = self._get_py_files('tests/')
            if self.with_integration:
                testfiles += self._get_py_files('tests/', 'integration/')
        if self.run_failed:
            nosecmd += ' --failed'
        nose = ' '.join(shlex.split(nosecmd) + testfiles)
        return nose

    def _remove_coverage(self):
        fn = '.coverage'
        if os.path.exists(fn):
            os.remove(fn)

    def run(self):
        cmds = [self._get_nose_command()]
        if not self.nose_only:
            self._no_print_statements()
            self._remove_coverage()
            cmds = [self.flake8] + cmds
        try:
            map(subprocess.check_call, map(shlex.split, cmds))
        except subprocess.CalledProcessError:
            raise SystemExit(-1)
        raise SystemExit(0)


setup(name='discviz',
      version=discviz.__version__,
      description='Discogs artist visualizer',
      long_description=open('README.md').read(),
      author='Steve Leonard',
      author_email='sleonard76@gmail.com',
      url='https://github.com/xsleonard/discviz',
      packages=['discviz'],
      include_package_data=True,
      install_requires=[],
      cmdclass=dict(test=Test),
      zip_safe=False,
      license='MIT')
