export namespace main {
	
	export class AppConfig {
	    cacheStrategy: string;
	
	    static createFrom(source: any = {}) {
	        return new AppConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.cacheStrategy = source["cacheStrategy"];
	    }
	}
	export class FileItem {
	    id: string;
	    path: string;
	    relativePath: string;
	    name: string;
	    type: string;
	
	    static createFrom(source: any = {}) {
	        return new FileItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.path = source["path"];
	        this.relativePath = source["relativePath"];
	        this.name = source["name"];
	        this.type = source["type"];
	    }
	}

}

