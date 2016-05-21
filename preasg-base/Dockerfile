FROM cern/slc6-base

RUN echo "/usr/local/lib" >> /etc/ld.so.conf.d/local.conf && \
    echo "/usr/local/lib64" >> /etc/ld.so.conf.d/local.conf

RUN yum groupinstall -y "Development Tools"
RUN yum install -y git tar libmpc-devel mpfr-devel gmp-devel tar bzip2 git make  wget

RUN mkdir /code_gcc && cd /code_gcc && \
    curl -O ftp://ftp.mirrorservice.org/sites/sourceware.org/pub/gcc/releases/gcc-4.8.4/gcc-4.8.4.tar.bz2 && \
    tar xvfj gcc-4.8.4.tar.bz2 && \
    cd gcc-4.8.4 && \
    ./configure --disable-multilib --enable-languages=c,c++,fortran && \
    make -j4 && make install && \
    cd / && rm -rf /code_gcc && ldconfig && ldconfig -p

ENV CC /usr/local/bin/gcc
ENV CXX /usr/local/bin/g++

RUN rpm --import http://emisoft.web.cern.ch/emisoft/dist/EMI/3/RPM-GPG-KEY-emi
RUN curl -o /etc/yum.repos.d/egi-trustanchors.repo \
            http://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.repo

RUN yum --nogpgcheck -y install yum-priorities yum-protectbase ca-policy-egi-core
RUN curl -O http://emisoft.web.cern.ch/emisoft/dist/EMI/3/sl6/x86_64/base/emi-release-3.0.0-2.el6.noarch.rpm && \
    yum localinstall -y emi-release-3.0.0-2.el6.noarch.rpm && \
    rm emi-release-3.0.0-2.el6.noarch.rpm
RUN yum install -y voms-clients3 globus-proxy-utils

RUN mkdir -p /etc/grid-security/vomsdir/atlas
ADD lcg-voms2.cern.ch.lsc /etc/grid-security/vomsdir/atlas/lcg-voms2.cern.ch.lsc
ADD voms2.cern.ch.lsc /etc/grid-security/vomsdir/atlas/voms2.cern.ch.lsc

RUN mkdir -p /etc/vomses
ADD atlas-lcg-voms2.cern.ch /etc/vomses/atlas-lcg-voms2.cern.ch
ADD atlas-lcg-voms2.cern.ch /etc/vomses/atlas-voms2.cern.ch

RUN git clone git://github.com/PanDAWMS/panda-client.git && \
    cd panda-client && python setup.py install && \
    rm -rf panda-client.git

ENV PATHENA_GRID_SETUP_SH /dev/null

RUN yum install -y \
       	cmake which zlib zlib-devel krb5-devel krb5-libs krb5-appl-clients \
        binutils libX11-devel libXpm-devel libXft-devel libXext-devel \
        openssl-devel pcre-devel mesa-libGL-devel mesa-libGLU-devel glew-devel \
        ftgl-devel mysql-devel fftw-devel cfitsio-devel graphviz-devel avahi-compat-libdns_sd-devel \
        libldap-dev python-devel libxml2-devel gsl-static

RUN curl -O http://eos.cern.ch/rpms/eos-aquamarine/slc-6-x86_64/eos-client-0.3.84-aquamarine.slc6.x86_64.rpm && \
    yum -y localinstall eos-client-0.3.84-aquamarine.slc6.x86_64.rpm && \
    rm eos-client-0.3.84-aquamarine.slc6.x86_64.rpm

RUN git clone --depth 1 https://github.com/xrootd/xrootd.git -b stable-4.2.x  && \
    cd xrootd && \
    mkdir xrootd-build && \
    cd xrootd-build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local -DENABLE_PERL=FALSE -DENABLE_FUSE=FALSE && \
    make && make install && \
    cd / && rm -rf xrootd

RUN mkdir -p /code_python && cd /code_python && \
    curl https://www.python.org/ftp/python/2.7.4/Python-2.7.4.tgz | tar -xzvf - && \
    cd Python-2.7.4 && \
    ./configure --prefix=/usr/local --enable-shared && \
    make -j4 && \
    make install && \
    cd / && rm -rf /code_python && ldconfig

RUN curl https://bootstrap.pypa.io/get-pip.py | python -
ADD custom_ssh_config /etc/ssh/ssh_config

