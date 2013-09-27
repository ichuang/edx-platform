###
### Script for editing the course's tabs
###

#
# Run it this way:
#   ./manage.py cms --settings dev edit_course_tabs --course Stanford/CS99/2013_spring
# Or via rake:
#   rake django-admin[edit_course_tabs,cms,dev,"--course Stanford/CS99/2013_spring --delete 4"]
#
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from .prompt import query_yes_no

from courseware.courses import get_course_by_id

from contentstore.views import tabs
from xmodule.exceptions import NotAllowedError


def print_course(course):
    "Prints out the course id and a numbered list of tabs."
    print course.id
    count = 1
    for item in course.tabs:
        print count, '"' + item.get('type') + '"', '"' + item.get('name', '') + '"'
        count += 1


# course.tabs looks like this
# [{u'type': u'courseware'}, {u'type': u'course_info', u'name': u'Course Info'}, {u'type': u'textbooks'},
# {u'type': u'discussion', u'name': u'Discussion'}, {u'type': u'wiki', u'name': u'Wiki'},
# {u'type': u'progress', u'name': u'Progress'}]


class Command(BaseCommand):
    help = """See and edit a course's tabs list.
The tabs are numbered starting with 1.
Tabs 1 and 2 cannot be changed, and tabs of type
static_tab cannot be edited (use Studio for those).
"""
    # Making these option objects separately, so can refer to their .help below
    create_option = make_option('--course',
                                action='store',
                                dest='course',
                                default=False,
                                help='--course <id> required, e.g. Stanford/CS99/2013_spring')
    delete_option = make_option('--delete',
                                action='store_true',
                                dest='delete',
                                default=False,
                                help='--delete <tab-number>')
    insert_option = make_option('--insert',
                                action='store_true',
                                dest='insert',
                                default=False,
                                help='--insert <tab-number> <type> <name>, e.g. 2 "course_info" "Course Info"')

    option_list = BaseCommand.option_list + (create_option, delete_option, insert_option)

    def handle(self, *args, **options):
        if not options['course']:
            raise CommandError(Command.create_option.help)

        course = get_course_by_id(options['course'])

        print 'Warning: this command directly edits the list of course tabs in mongo.'
        print 'Tabs before any changes:'
        print_course(course)

        try:
            if options['delete']:
                if len(args) != 1:
                    raise CommandError(Command.delete_option.help)
                num = int(args[0])
                if query_yes_no('Deleting tab {0} Confirm?'.format(num), default='no'):
                    tabs.primitive_delete(course, num)
            elif options['insert']:
                if len(args) != 3:
                    raise CommandError(Command.insert_option.help)
                num = int(args[0])
                typ = args[1]
                name = args[2]
                if query_yes_no('Inserting tab {0} "{1}" "{2}" Confirm?'.format(num, typ, name), default='no'):
                    tabs.primitive_insert(course, num, args[1], args[2])
        except NotAllowedError as e:
            # Cute: translate NotAllowedError to CommandError so the CLI error
            # prints nicely.
            raise CommandError(e)
