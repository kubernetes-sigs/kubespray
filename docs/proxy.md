# Setting up Environment Proxy

If you set http and https proxy, all nodes and loadbalancer will be excluded from proxy with generating no_proxy variable in `roles/kubespray-defaults/defaults/main.yml`, if you have additional resources for exclude add them to `additional_no_proxy` variable. If you want fully override your `no_proxy` setting, then fill in just `no_proxy` and no nodes or loadbalancer addresses will be added to no_proxy.

## Set proxy for http and https

 `http_proxy:"http://example.proxy.tld:port"`
 `https_proxy:"http://example.proxy.tld:port"`

## Set default no_proxy (this will override default no_proxy generation)

`no_proxy: "node1,node1_ip,node2,node2_ip...additional_host"`

## Set additional addresses to default no_proxy (all cluster nodes and loadbalancer)

`additional_no_proxy: "aditional_host,"`
