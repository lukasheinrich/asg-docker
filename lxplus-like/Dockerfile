FROM cern/slc6-base
ADD . /dockerbuild
WORKDIR /dockerbuild
RUN cp yum-puppet.repos.d/*.repo /etc/yum.repos.d
RUN cat lxplus_enabled_repos|grep "repo id.*repo name.*status" -A10000|grep -vE 'repolist|repo name'| \
    awk '{print $1}'|while read r;do yum-config-manager --enable $r;done

RUN cat lxplus_disabled_repos|grep "repo id.*repo name.*status" -A10000|grep -vE 'repolist|repo name'| \
    awk '{print $1}'|while read r;do yum-config-manager --disable $r;done
RUN yum install -y $(cat lxplus_yum_installed|grep "Installed Packages" -A10000 |grep -v "Installed Packages"|less|awk '{print $1}'|tr '\n' ' ')