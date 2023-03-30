// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.provide("dontmanage.help");

dontmanage.help.youtube_id = {};

dontmanage.help.has_help = function (doctype) {
	return dontmanage.help.youtube_id[doctype];
};

dontmanage.help.show = function (doctype) {
	if (dontmanage.help.youtube_id[doctype]) {
		dontmanage.help.show_video(dontmanage.help.youtube_id[doctype]);
	}
};

dontmanage.help.show_video = function (youtube_id, title) {
	if (dontmanage.utils.is_url(youtube_id)) {
		const expression =
			'(?:youtube.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu.be/)([^"&?\\s]{11})';
		youtube_id = youtube_id.match(expression)[1];
	}

	// (dontmanage.help_feedback_link || "")
	let dialog = new dontmanage.ui.Dialog({
		title: title || __("Help"),
		size: "large",
	});

	let video = $(
		`<div class="video-player" data-plyr-provider="youtube" data-plyr-embed-id="${youtube_id}"></div>`
	);
	video.appendTo(dialog.body);

	dialog.show();
	dialog.$wrapper.addClass("video-modal");

	let plyr;
	dontmanage.utils.load_video_player().then(() => {
		plyr = new dontmanage.Plyr(video[0], {
			hideControls: true,
			resetOnEnd: true,
		});
	});

	dialog.onhide = () => {
		plyr?.destroy();
	};
};

$("body").on("click", "a.help-link", function () {
	var doctype = $(this).attr("data-doctype");
	doctype && dontmanage.help.show(doctype);
});
