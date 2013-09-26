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
# for saving
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.django import modulestore


# These do_xxx functions don't have a lot of UI. Someday we could
# implement a GUI that calls down to pretty similar code.

def do_print(course):
    "Prints out the course id and a numbered list of tabs."
    print course.id
    count = 1
    for item in course.tabs:
        print count, '"' + item.get('type') + '"', '"' + item.get('name', '') + '"'
        count += 1

def do_delete(course, num):
    "Deletes the given tab number (error if num=1)"
    if num == 1:
        raise CommandError('Tab number 1 cannot be deleted')
    tabs = course.tabs
    del tabs[num - 1]  # -1 due to our 1-based indexing
    do_save(course)
    print "*Deleted*"
    do_print(course)

def do_insert(course, num, t, name):
    "Inserts a new tab at the given number (error if num=1)"
    if num == 1:
        raise CommandError('Tab number 1 cannot be changed')
    new_tab = {u'type': unicode(t), u'name': unicode(name)}
    tabs = course.tabs
    tabs.insert(num - 1, new_tab)  # -1 as above
    do_save(course)
    print '*Inserted*'
    do_print(course)

def do_save(course):
    "Saves the course back to modulestore."
    # This code copied from
    #  ~/edx_all/edx-platform/cms/djangoapps/contentstore/views/tabs.py
    course.save()
    modulestore('direct').update_metadata(course.location, own_metadata(course))

# course.tabs look like this
# [{u'type': u'courseware'}, {u'type': u'course_info', u'name': u'Course Info'}, {u'type': u'textbooks'},
# {u'type': u'discussion', u'name': u'Discussion'}, {u'type': u'wiki', u'name': u'Wiki'},
# {u'type': u'progress', u'name': u'Progress'}]


class Command(BaseCommand):
    help = """See and edit a course's tabs list.
The tabs are numbered starting with 1.
Tab number 1 cannot be changed.
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
        do_print(course)

        if options['delete']:
            if len(args) != 1:
                raise CommandError(Command.delete_option.help)
            num = int(args[0])
            if query_yes_no('Deleting tab {0} Confirm?'.format(num), default='no'):
                do_delete(course, num)
        elif options['insert']:
            if len(args) != 3:
                raise CommandError(Command.insert_option.help)
            num = int(args[0])
            typ = args[1]
            name = args[2]
            if query_yes_no('Inserting tab {0} "{1}" "{2}" Confirm?'.format(num, typ, name), default='no'):
                do_insert(course, num, args[1], args[2])

