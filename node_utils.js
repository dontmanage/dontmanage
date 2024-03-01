const fs = require("fs");
const path = require("path");
const redis = require("@redis/client");
const bench_path = path.resolve(__dirname, "..", "..");

const dns = require("dns");

// Since node17, node resolves to ipv6 unless system is configured otherwise.
// In DontManage context using ipv4 - 127.0.0.1 is fine.
dns.setDefaultResultOrder("ipv4first");

function get_conf() {
	// defaults
	var conf = {
		socketio_port: 9000,
	};

	var read_config = function (file_path) {
		const full_path = path.resolve(bench_path, file_path);

		if (fs.existsSync(full_path)) {
			var bench_config = JSON.parse(fs.readFileSync(full_path));
			for (var key in bench_config) {
				if (bench_config[key]) {
					conf[key] = bench_config[key];
				}
			}
		}
	};

	// get ports from bench/config.json
	read_config("config.json");
	read_config("sites/common_site_config.json");

	// set overrides from environment
	if (process.env.DONTMANAGE_SITE) {
		conf.default_site = process.env.DONTMANAGE_SITE;
	}
	if (process.env.DONTMANAGE_REDIS_CACHE) {
		conf.redis_cache = process.env.DONTMANAGE_REDIS_CACHE;
	}
	if (process.env.DONTMANAGE_REDIS_QUEUE) {
		conf.redis_queue = process.env.DONTMANAGE_REDIS_QUEUE;
	}
	if (process.env.DONTMANAGE_SOCKETIO_PORT) {
		conf.socketio_port = process.env.DONTMANAGE_SOCKETIO_PORT;
	}
	return conf;
}

function get_redis_subscriber(kind = "redis_queue", options = {}) {
	const conf = get_conf();
	const host = conf[kind];
	return redis.createClient({ url: host, ...options });
}

module.exports = {
	get_conf,
	get_redis_subscriber,
};
