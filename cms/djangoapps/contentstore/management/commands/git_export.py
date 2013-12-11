"""
This command exports a course from CMS to a git repository.
It takes as arguments the course id to export (i.e MITx/999/2020 ) and
the repository to commit too.  It takes username as an option for identifying
the commit, as well as a directory path to place the git repository.

By default it will use settings.GIT_REPO_EXPORT_DIR/repo_name as the cloned
directory.  It is branch aware, but will reset all local changes to the
repository before attempting to export the XML, add, and commit changes if
any have taken place.

This functionality is also available as an export view in studio if the giturl
attribute is set and the FEATURE['ENABLE_EXPORT_GIT'] is set.
"""

import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

import contentstore.git_export_utils as git_export_utils

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Take a course from studio and export it to a git repository.
    """

    option_list = BaseCommand.option_list + (
        make_option('--user', '-u', dest='user',
                    help='Add a user to the commit message.'),
        make_option('--repo_dir', '-r', dest='repo',
                    help='Specify existing git repo directory.'),
    )

    help = _('Take the specified course and attempt to '
             'export it to a git repository\n. Course directory '
             'must already be a git repository. Usage: '
             ' git_export <course_loc> <git_url>')

    def handle(self, *args, **options):
        """
        Checks arguments and runs export function if they are good
        """

        if len(args) != 2:
            raise CommandError('This script requires exactly two arguments: '
                               'course_loc and git_url')

        # Rethrow GitExportError as CommandError for SystemExit
        try:
            git_export_utils.export_to_git(
                args[0],
                args[1],
                options.get('user', ''),
                options.get('rdir', None)
            )
        except git_export_utils.GitExportError as ex:
            raise CommandError(str(ex))