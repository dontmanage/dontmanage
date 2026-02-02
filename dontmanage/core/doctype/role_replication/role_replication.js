// Copyright (c) 2024, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Role Replication", {
	refresh(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Replicate"), ($btn) => {
			$btn.text(__("Replicating..."));
			dontmanage.run_serially([
				() => dontmanage.dom.freeze("Replicating..."),
				() => frm.call("replicate_role"),
				() => dontmanage.dom.unfreeze(),
				() => dontmanage.msgprint(__("Replication completed.")),
				() => $btn.text(__("Replicate")),
			]);
		});
	},
});
