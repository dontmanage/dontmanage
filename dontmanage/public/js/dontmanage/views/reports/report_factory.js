// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.views.ReportFactory = class ReportFactory extends dontmanage.views.Factory {
	make(route) {
		const _route = ["List", route[1], "Report"];

		if (route[2]) {
			// custom report
			_route.push(route[2]);
		}

		dontmanage.set_route(_route);
	}
};
