sudo gbp buildpackage --git-ignore-new --git-builder=dpkg-buildpackage --git-debian-branch="$(git rev-parse --abbrev-ref HEAD)" -uc -us --build=any
