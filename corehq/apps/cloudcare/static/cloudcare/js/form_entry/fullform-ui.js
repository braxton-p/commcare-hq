/* global DOMPurify, mdAnchorRender */
hqDefine("cloudcare/js/form_entry/fullform-ui", function () {
    var Const = hqImport("cloudcare/js/form_entry/const"),
        Utils = hqImport("cloudcare/js/form_entry/utils");
    var md = window.markdownit();
    var groupNum = 0;

    //Overriden by downstream contexts, check before changing
    window.mdAnchorRender = md.renderer.rules.link_open || function (tokens, idx, options, env, self) {
        return self.renderToken(tokens, idx, options);
    };

    md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
        // If you are sure other plugins can't add `target` - drop check below
        var aIndex = tokens[idx].attrIndex('target');

        if (aIndex < 0) {
            tokens[idx].attrPush(['target', '_blank']); // add new attribute
        } else {
            tokens[idx].attrs[aIndex][1] = '_blank';    // replace value of existing attr
        }

        // pass token to default renderer.
        return mdAnchorRender(tokens, idx, options, env, self);
    };

    _.delay(function () {
        ko.bindingHandlers.renderMarkdown = {
            update: function (element, valueAccessor) {
                var value = ko.unwrap(valueAccessor());
                value = md.render(value || '');
                $(element).html(value);
            },
        };
    });

    //if index is part of a repeat, return only the part beyond the deepest repeat
    function relativeIndex(ix) {
        var steps = ix.split(',');
        var deepestRepeat = -1,
            i;
        for (i = steps.length - 2; i >= 0; i--) {
            if (steps[i].indexOf(':') !== -1) {
                deepestRepeat = i;
                break;
            }
        }
        if (deepestRepeat === -1) {
            return ix;
        } else {
            var relIx = '-';
            for (i = deepestRepeat + 1; i < steps.length; i++) {
                relIx += steps[i] + (i < steps.length - 1 ? ',' : '');
            }
            return relIx;
        }
    }

    function getIx(o) {
        var ix = o.rel_ix();
        while (ix[0] == '-') {
            o = o.parent;
            if (!o || ko.utils.unwrapObservable(o.rel_ix) === undefined) {
                break;
            }
            if (o.rel_ix().split(',').slice(-1)[0].indexOf(':') !== -1) {
                ix = o.rel_ix() + ',' + ix.substring(1);
            }
        }
        return ix;
    }

    function getForIx(o, ix) {
        if (ko.utils.unwrapObservable(o.type) === 'question') {
            return (getIx(o) === ix ? o : null);
        } else {
            for (var i = 0; i < o.children().length; i++) {
                var result = getForIx(o.children()[i], ix);
                if (result) {
                    return result;
                }
            }
        }
    }

    function parseMeta(type, style) {
        var meta = {};

        if (type === "date") {
            meta.mindiff = style.before !== null ? +style.before : null;
            meta.maxdiff = style.after !== null ? +style.after : null;
        } else if (type === "int" || type === "float") {
            meta.unit = style.unit;
        } else if (type == 'str') {
            meta.autocomplete = (style.mode === 'autocomplete');
            meta.autocomplete_key = style["autocomplete-key"];
            meta.mask = style.mask;
            meta.prefix = style.prefix;
            meta.longtext = (style.raw === 'full');
        } else if (type === "multiselect") {
            if (style["as-select1"]) {
                meta.as_single = [];
                var vs = style["as-select1"].split(',');
                for (var i = 0; i < vs.length; i++) {
                    var k = +vs[i];
                    if (k !== 0) {
                        meta.as_single.push(k);
                    }
                }
            }
        }

        if (type === "select" || type === "multiselect") {
            meta.appearance = style.raw;
        }

        return meta;
    }

    /**
     * Base abstract prototype for Repeat, Group and Form. Adds methods to
     * objects that contain a children array for rendering nested questions.
     * @param {Object} json - The JSON returned from touchforms to represent the container
     */
    function Container(json) {
        var self = this;
        self.pubsub = new ko.subscribable();
        self.fromJS(json);

        /**
         * Used in KO template to determine what template to use for a child
         * @param {Object} child - The child object to be rendered, either Group, Repeat, or Question
         */
        self.childTemplate = function (child) {
            return ko.utils.unwrapObservable(child.type) + '-fullform-ko-template';
        };

        self.hasError = ko.computed(function () {
            return _.find(self.children(), function (child) {
                return child.hasError();
            });
        });
    }

    /**
     * Reconciles the JSON representation of a Container (Group, Repeat, Form) and renders it into
     * a knockout representation.
     * @param {Object} json - The JSON returned from touchforms to represent a Container
     */
    Container.prototype.fromJS = function (json) {
        var self = this;
        var mapping = {
            caption: {
                update: function (options) {
                    return options.data ? DOMPurify.sanitize(options.data.replace(/\n/g, '<br/>')) : null;
                },
            },
            caption_markdown: {
                update: function (options) {
                    return options.data ? md.render(options.data) : null;
                },
            },
            children: {
                create: function (options) {
                    if (options.data.type === Const.QUESTION_TYPE) {
                        return new Question(options.data, self);
                    } else if (options.data.type === Const.GROUP_TYPE) {
                        return new Group(options.data, self);
                    } else if (options.data.type === Const.REPEAT_TYPE) {
                        return new Repeat(options.data, self);
                    } else {
                        console.error('Could not find question type of ' + options.data.type);
                    }
                },
                update: function (options) {
                    if (options.target.pendingAnswer &&
                            options.target.pendingAnswer() !== Const.NO_PENDING_ANSWER) {
                        // There is a request in progress
                        if (Utils.answersEqual(options.data.answer, options.target.pendingAnswer())) {
                            // We can now mark it as not dirty
                            options.data.answer = _.clone(options.target.pendingAnswer());
                            options.target.pendingAnswer(Const.NO_PENDING_ANSWER);
                        } else {
                            // still dirty, keep answer the same as the pending one
                            options.data.answer = _.clone(options.target.pendingAnswer());
                        }
                    }

                    // Do not update the answer if there is a server error on that question
                    if (ko.utils.unwrapObservable(options.target.serverError)) {
                        options.data.answer = _.clone(options.target.answer());
                    }
                    if (options.target.choices && _.isEqual(options.target.choices(), options.data.choices)) {
                        // replacing the full choice list if it has a few thousand items
                        // is actually quite expensive and can freeze the page for seconds.
                        // at the very least we can skip entirely when there's no change.
                        delete options.data.choices;
                    }
                    return options.target;
                },
                key: function (data) {
                    return ko.utils.unwrapObservable(data.uuid) || ko.utils.unwrapObservable(data.ix);
                },
            },
        };
        ko.mapping.fromJS(json, mapping, self);
    };

    /**
     * Represents the entire form. There is only one of these on a page.
     * @param {Object} json - The JSON returned from touchforms to represent a Form
     */
    function Form(json) {
        var self = this;
        self.displayOptions = json.displayOptions || {};
        json.children = json.tree;
        delete json.tree;
        Container.call(self, json);
        self.blockSubmit = ko.observable(false);
        self.isSubmitting = ko.observable(false);
        self.submitClass = Const.LABEL_OFFSET + ' ' + Const.CONTROL_WIDTH;

        self.currentIndex = ko.observable("0");
        self.atLastIndex = ko.observable(false);
        self.atFirstIndex = ko.observable(true);
        self.shouldAutoSubmit = json.shouldAutoSubmit;

        var _updateIndexCallback = function (ix, isAtFirstIndex, isAtLastIndex) {
            self.currentIndex(ix.toString());
            self.atFirstIndex(isAtFirstIndex);
            self.atLastIndex(isAtLastIndex);
        };

        self.showInFormNavigation = ko.computed(function () {
            return self.displayOptions.oneQuestionPerScreen !== undefined
            && self.displayOptions.oneQuestionPerScreen() === true;
        });

        self.isCurrentRequiredSatisfied = ko.computed(function () {
            if (!self.showInFormNavigation()) {
                return true;
            }

            return _.every(self.children(), function (q) {
                return (q.answer() === Const.NO_ANSWER && !q.required()) || q.answer() !== null;
            });
        });
        self.isCurrentRequiredSatisfied.subscribe(function (isSatisfied) {
            if (isSatisfied) {
                self.forceRequiredVisible(false);
            }
        });

        self.enableNextButton = ko.computed(function () {
            if (!self.showInFormNavigation()) {
                return false;
            }

            var allValidAndNotPending = _.every(self.children(), function (q) {
                return q.isValid() && !q.pendingAnswer();
            });
            return allValidAndNotPending
                && self.showInFormNavigation()
                && self.isCurrentRequiredSatisfied()
                && !self.atLastIndex();
        });

        self.enablePreviousButton = ko.computed(function () {
            if (!self.showInFormNavigation()) return false;
            return self.currentIndex() !== "0" && self.currentIndex() !== "-1" && !self.atFirstIndex();
        });

        self.enableSubmitButton = ko.computed(function () {
            return !self.isSubmitting();
        });

        self.submitText = ko.computed(function () {
            if (self.isSubmitting()) {
                return gettext('Submitting...');
            }
            return gettext('Submit');
        });

        self.forceRequiredVisible = ko.observable(false);

        self.showRequiredNotice = ko.computed(function () {
            return !self.isCurrentRequiredSatisfied() && self.forceRequiredVisible();
        });

        self.clickedNextOnRequired = function () {
            self.forceRequiredVisible(true);
        };

        self.enableForceNextButton = ko.computed(function () {
            return !self.isCurrentRequiredSatisfied() && !self.enableNextButton();
        });

        self.disableNextButton = ko.computed(function () {
            return !self.enableNextButton() && !self.enableForceNextButton();
        });

        self.showSubmitButton = ko.computed(function () {
            return !self.showInFormNavigation() && !self.shouldAutoSubmit;
        });

        self.submitForm = function () {
            $.publish('formplayer.' + Const.SUBMIT, self);
        };

        self.nextQuestion = function () {
            $.publish('formplayer.' + Const.NEXT_QUESTION, {
                callback: _updateIndexCallback,
                title: self.title(),
            });
        };

        self.prevQuestion = function () {
            $.publish('formplayer.' + Const.PREV_QUESTION, {
                callback: _updateIndexCallback,
                title: self.title(),
            });
        };

        self.afterRender = function () {
            $(document).on("click", ".help-text-trigger", function (event) {
                event.preventDefault();
                var container = $(event.currentTarget).closest(".caption");
                container.find(".modal").modal('show');
            });

            $(document).on("click", ".unsupported-question-type-trigger", function (event) {
                var container = $(event.currentTarget).closest(".widget");
                container.find(".modal").modal('show');
            });
        };

        $.unsubscribe('session');
        $.subscribe('session.reconcile', function (e, response, element) {
            // TODO where does response status parsing belong?
            if (response.status === 'validation-error') {
                if (response.type === 'required') {
                    element.serverError(gettext('An answer is required'));
                } else if (response.type === 'constraint') {
                    element.serverError(response.reason || gettext('This answer is outside the allowed range.'));
                }
                element.pendingAnswer(Const.NO_PENDING_ANSWER);
            } else {
                response.children = response.tree;
                delete response.tree;
                if (element.serverError) { element.serverError(null); }
                self.fromJS(response);
            }
        });

        $.subscribe('session.block', function (e, block) {
            $('#webforms input, #webforms textarea').prop('disabled', block === Const.BLOCK_ALL);
            self.blockSubmit(block === Const.BLOCK_ALL || block === Const.BLOCK_SUBMIT);
        });
    }
    Form.prototype = Object.create(Container.prototype);
    Form.prototype.constructor = Container;

    /**
     * Represents a group of questions.
     * @param {Object} json - The JSON returned from touchforms to represent a Form
     * @param {Object} parent - The object's parent. Either a Form, Group, or Repeat.
     */
    function Group(json, parent) {
        var self = this;
        Container.call(self, json);

        self.parent = parent;
        self.groupId = groupNum++;
        self.rel_ix = ko.observable(relativeIndex(self.ix()));
        self.isRepetition = parent instanceof Repeat;
        if (_.has(json, 'domain_meta') && _.has(json, 'style')) {
            self.domain_meta = parseMeta(json.datatype, json.style);
        }

        var styles = _.has(json, 'style') && json.style && json.style.raw ? json.style.raw.split(/\s+/) : [];
        self.collapsible = _.contains(styles, Const.COLLAPSIBLE);
        self.showChildren = ko.observable(!self.collapsible || _.contains(styles, Const.COLLAPSIBLE_OPEN));
        self.toggleChildren = function () {
            if (self.collapsible) {
                if (self.showChildren()) {
                    self.showChildren(false);
                } else {
                    self.showChildren(true);
                }
            }
        };

        self.captionId = function () {
            return "group_".concat(self.groupId).concat("_caption");
        };

        self.keyPressAction = function (data, event) {
            // Toggle children on Enter or Space.
            if (event.keyCode === 13 || event.keyCode === 32) {
                this.toggleChildren(data, event);
            }
        };

        self.childrenRequired = ko.computed(function () {
            return _.find(self.children(), function (child) {
                return child.required() || child.childrenRequired && child.childrenRequired();
            });
        });

        if (self.isRepetition) {
            // If the group is part of a repetition the index can change if the user adds or deletes
            // repeat groups.
            self.ix.subscribe(function () {
                self.rel_ix(relativeIndex(self.ix()));
            });
        }

        self.deleteRepeat = function () {
            $.publish('formplayer.' + Const.DELETE_REPEAT, self);
            $.publish('formplayer.dirty');
        };

        self.hasAnyNestedQuestions = function () {
            return _.any(self.children(), function (d) {
                if (d.type() === 'question' || d.type() === 'repeat-juncture') {
                    return true;
                } else if (d.type() === 'sub-group') {
                    return d.hasAnyNestedQuestions();
                }
            });
        };
    }
    Group.prototype = Object.create(Container.prototype);
    Group.prototype.constructor = Container;

    /**
     * Represents a repeat group. A repeat only has Group objects as children. Each child Group contains the
     * child questions to be rendered
     * @param {Object} json - The JSON returned from touchforms to represent a Form
     * @param {Object} parent - The object's parent. Either a Form, Group, or Repeat.
     */
    function Repeat(json, parent) {
        var self = this;
        Container.call(self, json);

        self.parent = parent;
        self.rel_ix = ko.observable(relativeIndex(self.ix()));
        if (_.has(json, 'domain_meta') && _.has(json, 'style')) {
            self.domain_meta = parseMeta(json.datatype, json.style);
        }
        self.templateType = 'repeat';
        self.ixInfo = function (o) {
            var fullIx = getIx(o);
            return o.rel_ix + (o.isRepetition ? '(' + o.uuid + ')' : '') + (o.rel_ix !== fullIx ? ' :: ' + fullIx : '');
        };

        self.newRepeat = function () {
            $.publish('formplayer.' + Const.NEW_REPEAT, self);
            $.publish('formplayer.dirty');
        };

        self.afterRender = function () {
            var addNewRepeatKey = 'repeat.dialog.add.new';
            if (self.parent.translations) {
                var addNewRepeatTranslation = ko.toJS(self.parent.translations[addNewRepeatKey]);
                if (addNewRepeatTranslation) {
                    $('#repeat-add-new').html(addNewRepeatTranslation);
                }
            }
        }
    }
    Repeat.prototype = Object.create(Container.prototype);
    Repeat.prototype.constructor = Container;

    /**
     * Represents a Question. A Question contains an Entry which is the widget that is displayed for that question
     * type.
     * child questions to be rendered
     * @param {Object} json - The JSON returned from touchforms to represent a Form
     * @param {Object} parent - The object's parent. Either a Form, Group, or Repeat.
     */
    function Question(json, parent) {
        var self = this;
        self.fromJS(json);
        self.parent = parent;
        // Grab the parent pubsub so questions can interact with other questions on the same form/group.
        self.parentPubSub = (parent) ? parent.pubsub : new ko.subscribable();
        self.error = ko.observable(null);
        self.serverError = ko.observable(null);
        self.rel_ix = ko.observable(relativeIndex(self.ix()));
        if (_.has(json, 'domain_meta') && _.has(json, 'style')) {
            self.domain_meta = parseMeta(json.datatype, json.style);
        }
        self.throttle = 200;
        self.controlWidth = Const.CONTROL_WIDTH;
        self.labelWidth = Const.LABEL_WIDTH;

        // If the question has ever been answered, set this to true.
        self.hasAnswered = false;

        // pendingAnswer is a copy of an answer being submitted, so that we know not to reconcile a new answer
        // until the question has received a response from the server.
        self.pendingAnswer = ko.observable(Const.NO_PENDING_ANSWER);
        self.pendingAnswer.subscribe(function () { self.hasAnswered = true; });
        self.dirty = ko.computed(function () {
            return self.pendingAnswer() !== Const.NO_PENDING_ANSWER;
        });
        self.clean = ko.computed(function () {
            return !self.dirty() && !self.error() && !self.serverError() && self.hasAnswered;
        });
        self.hasError = ko.computed(function () {
            return (self.error() || self.serverError()) && !self.dirty();
        });

        self.isValid = function () {
            return self.error() === null && self.serverError() === null;
        };

        self.is_select = (self.datatype() === 'select' || self.datatype() === 'multiselect');
        self.entry = hqImport("cloudcare/js/form_entry/entrycontrols_full").getEntry(self);
        self.entryTemplate = function () {
            return self.entry.templateType + '-entry-ko-template';
        };
        self.afterRender = function () { self.entry.afterRender(); };

        self.ixInfo = function (o) {
            var fullIx = getIx(o);
            return o.rel_ix + (o.isRepetition ? '(' + o.uuid + ')' : '') + (o.rel_ix !== fullIx ? ' :: ' + fullIx : '');
        };

        self.triggerAnswer = function () {
            self.pendingAnswer(_.clone(self.answer()));
            publishAnswerEvent();
        };
        var publishAnswerEvent = _.throttle(function () {
            $.publish('formplayer.dirty');
            $.publish('formplayer.' + Const.ANSWER, self);
        }, self.throttle);
        self.onchange = self.triggerAnswer;

        self.mediaSrc = function (resourceType) {
            if (!resourceType || !_.isFunction(Utils.resourceMap)) { return ''; }
            return Utils.resourceMap(resourceType);
        };
    }

    /**
     * Reconciles the JSON representation of a Question and renders it into
     * a knockout representation.
     * @param {Object} json - The JSON returned from touchforms to represent a Question
     */
    Question.prototype.fromJS = function (json) {
        var self = this;
        var mapping = {
            caption: {
                update: function (options) {
                    return options.data ? DOMPurify.sanitize(options.data.replace(/\n/g, '<br/>')) : null;
                },
            },
            caption_markdown: {
                update: function (options) {
                    return options.data ? md.render(options.data) : null;
                },
            },
        };

        ko.mapping.fromJS(json, mapping, self);
    };
    /**
     * Returns a list of style strings that match the given pattern.
     * If a regex is provided, returns regex matches. If a string is provided
     * an exact match is returned.
     * @param {Object} pattern - the regex or string used to find matching styles.
     */
    Question.prototype.stylesContaining = function (pattern) {
        var self = this;
        var retVal = [];
        var styleStr = (self.style) ? ko.utils.unwrapObservable(self.style.raw) : null;
        if (styleStr) {
            var styles = styleStr.split(' ');
            styles.forEach(function (style) {
                if ((pattern instanceof RegExp && style.match(pattern))
                    || (typeof pattern === "string" && pattern === style)) {
                    retVal.push(style);
                }
            });
        }
        return retVal;
    };
    /**
     * Returns a boolean of whether the styles contain a pattern
     * If a regex is provided, returns regex matches. If a string is provided
     * an exact match is returned.
     * @param {Object} pattern - the regex or string used to find matching styles.
     */
    Question.prototype.stylesContains = function (pattern) {
        return this.stylesContaining(pattern).length > 0;
    };

    return {
        getIx: getIx,
        getForIx: getForIx,
        Form: function (json) {
            return new Form(json);
        },
        Question: function (json, parent) {
            return new Question(json, parent);
        },
    };
});
