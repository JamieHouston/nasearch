/*jslint browser: true*/
/*global $, Mustache*/

(function () {
    "use strict";

    function TopicPopupView() {
        var self = this;
        self.template = $('#topic-list-template').html();
        self.selectedTemplate =
            $('#topic-selected-template').html();
        self.view = {};
        self.topics = {};

        self.click_unpicked = function (event) {
            var text = $(this).html().trim(),
                topic = self.topics[text],
                id = topic.id;
            $(this).hide();
            $(this).addClass('picked');
            $(".selected-topics").find("#topic" + id).show();
            console.log($(".selected-topics")
                .find("#topic" + id).length);
            event.stopPropagation();
        };

        self.click_picked = function (event) {
            var text = $(this).html().trim(),
                topic = self.topics[text],
                id = topic.id;
            $(this).hide();
            $(".topic-suggestions").find("#topic" + id)
                .show().removeClass('picked');
            event.stopPropagation();
        };

        self.render = function () {
            $('#topic-field').after(
                Mustache.render(self.template, self.view)
            );
            $('.selected-topics').append(
                Mustache.render(self.selectedTemplate,
                    {topics: self.view.topics.reverse()})
            );
        };

        self.getTopics = function () {
            function handleResponse(response) {
                var i,
                    topics = response;

                self.view = {
                    topics: topics
                };

                for (i = 0; i < topics.length; i += 1) {
                    self.topics[topics[i].text] = topics[i];
                }

                self.render();
                $(".topic-suggestions")
                    .find(".topic-suggestion")
                    .click(self.click_unpicked);
                $(".selected-topics")
                    .find(".topic-suggestion")
                    .click(self.click_picked);
            }

            $.get('topics', handleResponse);
        };

        // register event handlers
        $("#topic-field").keyup(function (event) {
            var string = $(this).val().toLowerCase();
            $(".topic-suggestions .topic-suggestion").each(
                function () {
                    var text = $(this).html().toLowerCase();
                    if (!$(this).hasClass('picked')) {
                        if (text.indexOf(string) !== -1) {
                            $(this).show();
                        } else {
                            $(this).hide();
                        }
                    }
                }
            );
        });

        // initialise data and render
        self.getTopics();
    }

    $(document).ready(function () {
        Mustache.tags = ["[[", "]]"];
        var topicPopupView = new TopicPopupView();

        function search() {
            $.get(
                'search',
                {"string": $("#search-field").val()},
                function (response) {
                    $("#content").html("");
                    $("#content").append(response);
                }
            );
        }

        $("#content").on("click", ".shownote-heading-div",
            function () {
                $(this).next().toggle(200);
            });

        $("#content").on("mouseenter", ".shownote-heading-div",
            function () {
                $(this).removeClass("bg-info");
                $(this).addClass("bg-primary");
            });

        $("#content").on("mouseleave", ".shownote-heading-div",
            function () {
                $(this).removeClass("bg-primary");
                $(this).addClass("bg-info");
            });

        $("#search-button").click(search);

        $("#search-field").keypress(function (e) {
            if (e.which === 13) {
                search();
            }
        });
    });
}());
