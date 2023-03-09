#!/bin/bash

set -o errexit
set -o pipefail
if [[ ${DEBUG:-false} == "true" ]]; then
    set -o xtrace
fi

checksums_file="$(git rev-parse --show-toplevel)/roles/download/defaults/main/checksums.yml"
downloads_folder=/tmp/kubespray_binaries

function get_versions {
    local type="$1"
    local name="$2"
    # NOTE: Limit in the number of versions to be register in the checksums file
    local limit="${3:-7}"
    local python_app="${4:-"import sys,re;tags=[tag.rstrip() for tag in sys.stdin if re.match(\'^v?(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)$\',tag)];print(\' \'.join(tags[:$limit]))"}"
    local version=""
    local attempt_counter=0
    readonly max_attempts=5

    until [ "$version" ]; do
        version=$("_get_$type" "$name" "$python_app")
        if [ "$version" ]; then
            break
        elif [ ${attempt_counter} -eq ${max_attempts} ]; then
            echo "Max attempts reached"
            exit 1
        fi
        attempt_counter=$((attempt_counter + 1))
        sleep $((attempt_counter * 2))
    done

    echo "${version}"
}

function _get_github_tags {
    local repo="$1"
    local python_app="$2"

    # The number of results per page (max 100).
    tags="$(curl -s "https://api.github.com/repos/$repo/tags?per_page=100")"
    if [ "$tags" ]; then
        echo "$tags" | grep -Po '"name":.*?[^\\]",' | awk -F '"' '{print $4}' | python -c "$python_app"
    fi
}

function _vercmp {
    local v1=$1
    local op=$2
    local v2=$3
    local result

    # sort the two numbers with sort's "-V" argument.  Based on if v2
    # swapped places with v1, we can determine ordering.
    result=$(echo -e "$v1\n$v2" | sort -V | head -1)

    case $op in
    "==")
        [ "$v1" = "$v2" ]
        return
        ;;
    ">")
        [ "$v1" != "$v2" ] && [ "$result" = "$v2" ]
        return
        ;;
    "<")
        [ "$v1" != "$v2" ] && [ "$result" = "$v1" ]
        return
        ;;
    ">=")
        [ "$result" = "$v2" ]
        return
        ;;
    "<=")
        [ "$result" = "$v1" ]
        return
        ;;
    *)
        echo "unrecognised op: $op"
        exit 1
        ;;
    esac
}

function get_checksums {
    local binary="$1"
    local version_exceptions="cri_dockerd_archive nerdctl_archive containerd_archive"
    declare -A skip_archs=(
["crio_archive"]="arm ppc64le"
["calicoctl_binary"]="arm"
["ciliumcli_binary"]="ppc64le"
["etcd_binary"]="arm"
["cri_dockerd_archive"]="arm ppc64le"
["runc"]="arm"
["crun"]="arm ppc64le"
["youki"]="arm arm64 ppc64le"
["kata_containers_binary"]="arm arm64 ppc64le"
["gvisor_runsc_binary"]="arm ppc64le"
["gvisor_containerd_shim_binary"]="arm ppc64le"
["containerd_archive"]="arm"
["skopeo_binary"]="arm ppc64le"
)
    echo "${binary}_checksums:" | tee --append "$checksums_file"
    for arch in arm arm64 amd64 ppc64le; do
        echo "  $arch:" | tee --append "$checksums_file"
        for version in "${@:2}"; do
            checksum=0
            [[ "${skip_archs[$binary]}" == *"$arch"* ]] || checksum=$(_get_checksum "$binary" "$version" "$arch")
            [[ "$version_exceptions" != *"$binary"* ]] || version=${version#v}
            echo "    $version: $checksum" | tee --append "$checksums_file"
        done
    done
}

function get_krew_archive_checksums {
    declare -A archs=(
["linux"]="arm arm64 amd64"
["darwin"]="arm64 amd64"
["windows"]="amd64"
)

    echo "krew_archive_checksums:" | tee --append "$checksums_file"
    for os in "${!archs[@]}"; do
        echo "  $os:" | tee --append "$checksums_file"
        for arch in arm arm64 amd64 ppc64le; do
            echo "    $arch:" | tee --append "$checksums_file"
            for version in "$@"; do
                checksum=0
                [[ " ${archs[$os]} " != *" $arch "* ]] || checksum=$(_get_checksum "krew_archive" "$version" "$arch" "$os")
                echo "      $version: $checksum" | tee --append "$checksums_file"
            done
        done
    done
}

function get_calico_crds_archive_checksums {
    echo "calico_crds_archive_checksums:" | tee --append "$checksums_file"
    for version in "$@"; do
        echo "  $version: $(_get_checksum "calico_crds_archive" "$version")" | tee --append "$checksums_file"
    done
}

function get_containerd_archive_checksums {
    declare -A support_version_history=(
["arm"]="2"
["arm64"]="1.6.0"
["amd64"]="1.5.5"
["ppc64le"]="1.6.7"
)

    echo "containerd_archive_checksums:" | tee --append "$checksums_file"
    for arch in arm arm64 amd64 ppc64le; do
        echo "  $arch:" | tee --append "$checksums_file"
        for version in "${@}"; do
            _vercmp "${version#v}" '>=' "${support_version_history[$arch]}" && checksum=$(_get_checksum "containerd_archive" "$version" "$arch") || checksum=0
            echo "    ${version#v}: $checksum" | tee --append "$checksums_file"
        done
    done
}

function _get_checksum {
    local binary="$1"
    local version="$2"
    local arch="${3:-amd64}"
    local os="${4:-linux}"
    local target="$downloads_folder/$binary/$version-$os-$arch"
    readonly github_url="https://github.com"
    readonly github_releases_url="$github_url/%s/releases/download/$version/%s"
    readonly github_archive_url="$github_url/%s/archive/%s"
    readonly google_url="https://storage.googleapis.com"
    readonly k8s_url="$google_url/kubernetes-release/release/$version/bin/$os/$arch/%s"

    # Download URLs
    declare -A urls=(
["crictl"]="$(printf "$github_releases_url" "kubernetes-sigs/cri-tools" "crictl-$version-$os-$arch.tar.gz")"
["crio_archive"]="$(printf "$github_releases_url" "cri-o/cri-o" "cri-o.$arch.$version.tar.gz")"
["kubelet"]="$(printf "$k8s_url" "kubelet")"
["kubectl"]="$(printf "$k8s_url" "kubectl")"
["kubeadm"]="$(printf "$k8s_url" "kubeadm")"
["etcd_binary"]="$(printf "$github_releases_url" "etcd-io/etcd" "etcd-$version-$os-$arch.tar.gz")"
["cni_binary"]="$(printf "$github_releases_url" "containernetworking/plugins" "cni-plugins-$os-$arch-$version.tgz")"
["calicoctl_binary"]="$(printf "$github_releases_url" "projectcalico/calico" "calicoctl-$os-$arch")"
["ciliumcli_binary"]="$(printf "$github_releases_url" "cilium/cilium-cli" "cilium-$os-$arch.tar.gz")"
["calico_crds_archive"]="$(printf "$github_archive_url" "projectcalico/calico" "$version.tar.gz")"
["krew_archive"]="$(printf "$github_releases_url" "kubernetes-sigs/krew" "krew-${os}_$arch.tar.gz")"
["helm_archive"]="https://get.helm.sh/helm-$version-$os-$arch.tar.gz"
["cri_dockerd_archive"]="$(printf "$github_releases_url" "Mirantis/cri-dockerd" "cri-dockerd-${version#v}.$arch.tgz")"
["runc"]="$(printf "$github_releases_url" "opencontainers/runc" "runc.$arch")"
["crun"]="$(printf "$github_releases_url" "containers/crun" "crun-$version-$os-$arch")"
["youki"]="$(printf "$github_releases_url" "containers/youki" "youki_$([ $version == "v0.0.1" ] && echo "v0_0_1" || echo "${version#v}" | sed 's|\.|_|g')_$os.tar.gz")"
["kata_containers_binary"]="$(printf "$github_releases_url" "kata-containers/kata-containers" "kata-static-$version-${arch//amd64/x86_64}.tar.xz")"
["gvisor_runsc_binary"]="$(printf "$google_url/gvisor/releases/release/$version/%s/runsc" "$(echo "$arch" | sed -e 's/amd64/x86_64/' -e 's/arm64/aarch64/')")"
["gvisor_containerd_shim_binary"]="$(printf "$google_url/gvisor/releases/release/$version/%s/containerd-shim-runsc-v1" "$(echo "$arch" | sed -e 's/amd64/x86_64/' -e 's/arm64/aarch64/')")"
["nerdctl_archive"]="$(printf "$github_releases_url" "containerd/nerdctl" "nerdctl-${version#v}-$os-$([ "$arch" == "arm" ] && echo "arm-v7" || echo "$arch" ).tar.gz")"
["containerd_archive"]="$(printf "$github_releases_url" "containerd/containerd" "containerd-${version#v}-$os-$arch.tar.gz")"
["skopeo_binary"]="$(printf "$github_releases_url" "lework/skopeo-binary" "skopeo-$os-$arch")"
["yq"]="$(printf "$github_releases_url" "mikefarah/yq" "yq_${os}_$arch")"
)

    mkdir -p "$(dirname $target)"
    [ -f "$target" ] || curl -LfSs -o "${target}" "${urls[$binary]}"
    sha256sum ${target} | awk '{print $1}'
}

function main {
    mkdir -p "$(dirname "$checksums_file")"
    echo "---" | tee "$checksums_file"
    get_checksums crictl $(get_versions github_tags kubernetes-sigs/cri-tools)
    get_checksums crio_archive $(get_versions github_tags cri-o/cri-o)
    kubernetes_versions=$(get_versions github_tags kubernetes/kubernetes 20)
    echo "# Checksum" | tee --append "$checksums_file"
    echo "# Kubernetes versions above Kubespray's current target version are untested and should be used with caution." | tee --append "$checksums_file"
    get_checksums kubelet $kubernetes_versions
    get_checksums kubectl $kubernetes_versions
    get_checksums kubeadm $kubernetes_versions
    get_checksums etcd_binary $(get_versions github_tags etcd-io/etcd)
    get_checksums cni_binary $(get_versions github_tags containernetworking/plugins)
    calico_versions=$(get_versions github_tags projectcalico/calico 20)
    get_checksums calicoctl_binary $calico_versions
    get_checksums ciliumcli_binary $(get_versions github_tags cilium/cilium-cli 10)
    get_calico_crds_archive_checksums $calico_versions
    get_krew_archive_checksums $(get_versions github_tags kubernetes-sigs/krew 2)
    get_checksums helm_archive $(get_versions github_tags helm/helm)
    get_checksums cri_dockerd_archive $(get_versions github_tags Mirantis/cri-dockerd)
    get_checksums runc $(get_versions github_tags opencontainers/runc 5)
    get_checksums crun $(get_versions github_tags containers/crun)
    get_checksums youki $(get_versions github_tags containers/youki)
    get_checksums kata_containers_binary $(get_versions github_tags kata-containers/kata-containers 10)
    gvisor_versions=$(get_versions github_tags google/gvisor 0 "import sys,re;tags=[tag[8:16] for tag in sys.stdin if re.match('^release-?(0|[1-9]\d*)\.(0|[1-9]\d*)$',tag)];print(' '.join(tags[:9]))")
    get_checksums gvisor_runsc_binary $gvisor_versions
    get_checksums gvisor_containerd_shim_binary $gvisor_versions
    get_checksums nerdctl_archive $(get_versions github_tags containerd/nerdctl)
    get_containerd_archive_checksums $(get_versions github_tags containerd/containerd 30)
    get_checksums skopeo_binary $(get_versions github_tags lework/skopeo-binary)
    get_checksums yq $(get_versions github_tags mikefarah/yq)
}

if [[ ${__name__:-"__main__"} == "__main__" ]]; then
    main
fi
