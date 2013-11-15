"""
Script for importing courseware from git/xml into a mongo modulestore
"""
import os
import sys
import re
import datetime
import StringIO
import logging

from django.utils.translation import ugettext as _
from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError, make_option

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore

import mongoengine
from dashboard.models import CourseImportLog

log = logging.getLogger(__name__)

GIT_REPO_DIR = getattr(settings, 'GIT_REPO_DIR', '/opt/edx/course_repos')
GIT_IMPORT_STATIC = getattr(settings, 'GIT_IMPORT_STATIC', True)

def add_repo(repo, rdir_in):
    """This will add a git repo into the mongo modulestore"""
    # pylint: disable-msg=R0915

    # Set defaults even if it isn't defined in settings
    mongo_db = {
        'host': 'localhost',
        'user': '',
        'password': '',
        'db': 'xlog',
    }

    # Allow overrides
    if hasattr(settings, 'MONGODB_LOG'):
        for config_item in ['host', 'user', 'password', 'db', ]:
            mongo_db[config_item] = settings.MONGODB_LOG.get(
                config_item, mongo_db[config_item])

    if not os.path.isdir(GIT_REPO_DIR):
        log.critical(_("Path {0} doesn't exist, please create it, or configure a "
                       "different path with GIT_REPO_DIR").format(GIT_REPO_DIR))
        return -1

    # -----------------------------------------------------------------------------
    # pull from git
    if not (repo.endswith('.git') or repo.startswith('http:') or
       repo.startswith('https:') or repo.startswith('git:')):

        log.error(_('Oops, not a git ssh url?'))
        log.error(_('Expecting something like git@github.com:mitocw/edx4edx_lite.git'))
        return -1

    if rdir_in:
        rdir = rdir_in
        rdir = os.path.basename(rdir)
    else:
        rdir = repo.rsplit('/', 1)[-1].rsplit('.git', 1)[0]

    log.debug('rdir = {0}'.format(rdir))

    rdirp = '{0}/{1}'.format(GIT_REPO_DIR, rdir)
    if os.path.exists(rdirp):
        log.info(_('directory already exists, doing a git pull instead of git clone'))
        cmd = 'cd {0}/{1}; git pull'.format(GIT_REPO_DIR, rdir)
    else:
        cmd = 'cd {0}; git clone "{1}"'.format(GIT_REPO_DIR, repo)

    log.debug(cmd)
    ret_git = os.popen(cmd).read()
    log.debug(ret_git)

    if not os.path.exists('{0}/{1}'.format(GIT_REPO_DIR, rdir)):
        log.error(_('git clone failed!'))
        return -1

    # get commit id
    commit_id = os.popen('cd {0}; git log -n 1 | head -1'.format(rdirp)).read().strip().split(' ')[1]

    ret_git += _('\nCommit ID: {0}').format(commit_id)

    # get branch
    branch = ''
    for k in os.popen('cd {0}; git branch'.format(rdirp)).readlines():
        if k[0] == '*':
            branch = k[2:].strip()

    ret_git += '   \nBranch: {0}'.format(branch)

    # Get XML logging logger and capture debug to parse results
    output = StringIO.StringIO()
    import_logger = logging.getLogger('xmodule.modulestore.xml_importer')
    git_logger = logging.getLogger('git_add_script')
    xml_logger = logging.getLogger('xmodule.modulestore.xml')
    xml_seq_logger = logging.getLogger('xmodule.seq_module')

    import_log_handler = logging.StreamHandler(output)
    import_log_handler.setLevel(logging.DEBUG)

    for logger in [import_logger, git_logger, xml_logger, xml_seq_logger, ]:
        logger.old_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(import_log_handler)

    try:
        management.call_command('import', GIT_REPO_DIR, rdir,
                                nostatic=not GIT_IMPORT_STATIC)
    except CommandError, ex:
        log.critical(_('Unable to run import command.'))
        log.critical(_('Error was {0}').format(str(ex)))
        return -1

    ret_import = output.getvalue()

    # Remove handler hijacks
    for logger in [import_logger, git_logger, xml_logger, xml_seq_logger, ]:
        logger.setLevel(logger.old_level)
        logger.removeHandler(import_log_handler)

    course_id = 'unknown'
    location = 'unknown'

    # extract course ID from output of import-command-run and make symlink
    # this is needed in order for custom course scripts to work
    match = re.search('(?ms)===> IMPORTING course to location ([^ \n]+)',
                      ret_import)
    if match:
        location = match.group(1).strip()
        log.debug('location = {0}'.format(location))
        course_id = location.replace('i4x://', '').replace(
            '/course/', '/').split('\n')[0].strip()

        cdir = '{0}/{1}'.format(GIT_REPO_DIR, course_id.split('/')[1])
        log.debug(_('Studio course dir = {0}').format(cdir))

        if os.path.exists(cdir) and not os.path.islink(cdir):
            log.debug(_('   -> exists, but is not symlink'))
            log.debug(os.popen('ls -l {0}'.format(cdir)).read())
            log.debug(os.popen('rmdir {0}'.format(cdir)).read())

        if not os.path.exists(cdir):
            log.debug(_('   -> creating symlink'))
            log.debug(os.popen('ln -s {0} {1}'.format(rdirp,
                      cdir)).read())
            log.debug(os.popen('ls -l {0}'.format(cdir)).read())

    # -----------------------------------------------------------------------------
    # store import-command-run output in mongo
    mongouri = 'mongodb://{0}:{1}@{2}/{3}'.format(
        mongo_db['user'], mongo_db['password'],
        mongo_db['host'], mongo_db['db'])

    try:
        if mongo_db['user'] and mongo_db['password']:
            mdb = mongoengine.connect(mongo_db['db'], host=mongouri)
        else:
            mdb = mongoengine.connect(mongo_db['db'], host=mongo_db['host'])
    except mongoengine.connection.ConnectionError, ex:
        log.critical(_('Unable to connect to mongodb to save log, please '
                       'check MONGODB_LOG settings'))
        log.critical(_('Error was: {0}').format(str(ex)))
        return -1
    cil = CourseImportLog(
        course_id=course_id,
        location=location,
        repo_dir=rdir,
        created=datetime.datetime.now(),
        import_log=ret_import,
        git_log=ret_git,
    )
    cil.save()

    log.debug(_('saved CourseImportLog for {0}').format(cil.course_id))
    mdb.disconnect()
    return 0

class Command(BaseCommand):
    """
    Pull a git repo and import into the mongo based content database.
    """

    help = _('Import the specified git repository into the modulestore and directory')

    def handle(self, *args, **options):
        """Check inputs and run the command"""
        # pylint: disable-msg=C0103

        if isinstance(modulestore, XMLModuleStore):
            raise CommandError(_('This script requires a mongo module store'))

        if len(args) < 1:
            raise CommandError(_('This script requires at least one argument, the git URL'))

        if len(args) > 2:
            raise CommandError(_('This script requires no more than two arguments.'))

        rdir_arg = None

        if len(args) > 1:
            rdir_arg = args[1]

        if add_repo(args[0], rdir_arg) != 0:
            raise CommandError(_('Repo was not added, check log output for details'))
