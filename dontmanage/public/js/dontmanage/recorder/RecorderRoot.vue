<template>
	<keep-alive include="RecorderDetail">
		<router-view/>
	</keep-alive>
</template>

<script>
export default {
	name: "RecorderRoot",
	watch: {
		async $route() {
			dontmanage.router.current_route = await dontmanage.router.parse();
			dontmanage.breadcrumbs.update();
		}
	}
};
</script>
