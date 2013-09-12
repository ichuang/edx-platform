(function (window, undefined) {
    Transcripts.MessageManager = Backbone.View.extend({
        tagName: 'div',
        elClass: '.wrapper-transcripts-message',
        invisibleClass: 'is-invisible',

        events: {
            'click .setting-import': 'importHandler',
            'click .setting-replace': 'importHandler',
            'click .setting-choose': 'chooseHandler',
            // 'click ': handler,
            // 'click ': handler,
            // 'click ': handler
        },

        templates: {
            not_found: '#transcripts-not-found',
            found: '#transcripts-found',
            import: '#transcripts-import',
            replace:  '#transcripts-replace',
            uploaded:  '#transcripts-uploaded',
            use_existing: '#transcripts-use-existing',
            choose: '#transcripts-choose'
        },

        initialize: function () {
            _.bindAll(this);

            this.fileUploader = new Transcripts.FileUploader({
                el: this.$el,
                messenger: this,
                component_id: this.options.component_id
            });
        },

        render: function (template, params) {
            var tpl = $(this.templates[template]).text(),
                videoList = this.options.parent.getVideoObjectsList(),
                groupedList = _.groupBy(
                    videoList,
                    function (value) {
                        return value.video;
                    }
                ),
                html5List = params.html5_local;

            if (!tpl) {
                console.error('Couldn\'t load Transcripts status template');
            }
            this.template = _.template(tpl);
            this.$el
                .removeClass('is-invisible')
                .find(this.elClass).html(this.template({
                    component_id: encodeURIComponent(this.options.component_id),
                    html5_list: html5List,
                    grouped_list: groupedList
                }));

            this.fileUploader.render();

            return this;
        },

        showError: function (err, hideButtons) {
            var $error = this.$el.find('.transcripts-error-message');

            if (err) {
                // Hide any other error messages.
                this.hideError();

                $error
                    .html(gettext(err))
                    .removeClass(this.invisibleClass);

                if (hideButtons) {
                    this.$el.find('.wrapper-transcripts-buttons')
                        .addClass(this.invisibleClass);
                }
            }
        },

        hideError: function () {
            this.$el.find('.transcripts-error-message')
                .addClass(this.invisibleClass);

            this.$el.find('.wrapper-transcripts-buttons')
                .removeClass(this.invisibleClass);
        },

        importHandler: function (event) {
            event.preventDefault();

            this.importTranscripts();
        },

        importTranscripts: function () {
            var self = this,
                utils = Transcripts.Utils,
                component_id = this.options.component_id,
                videoList = this.options.parent.getVideoObjectsList();

            utils.command('import', component_id, videoList)
                .done(function (resp) {
                    // TODO: update subs field

                    self.render('found');
                })
                .fail(function (resp) {
                    self.showError('Error: Import failed.');
                });
        }

    });
}(this));