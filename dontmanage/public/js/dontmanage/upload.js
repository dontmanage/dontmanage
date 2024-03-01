// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

if (dontmanage.require) {
	dontmanage.require("file_uploader.bundle.js");
} else {
	dontmanage.ready(function () {
		dontmanage.require("file_uploader.bundle.js");
	});
}
