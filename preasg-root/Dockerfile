FROM lukasheinrich/preasg-base

RUN yum groupinstall -y "Development Tools"
RUN yum install -y \
        libmpc-devel mpfr-devel gmp-devel tar bzip2 git make binutils libX11-devel libXpm-devel libXft-devel libXext-devel \
        openssl-devel pcre-devel mesa-libGL-devel mesa-libGLU-devel glew-devel \
        ftgl-devel mysql-devel fftw-devel cfitsio-devel graphviz-devel avahi-compat-libdns_sd-devel \
        libldap-dev python-devel libxml2-devel gsl-static

RUN curl -s http://linuxsoft.cern.ch/cern/devtoolset/slc6-devtoolset.repo -o /etc/yum.repos.d/slc6-devtoolset.repo

RUN mkdir /code_gcc && cd /code_gcc && \
    curl -O ftp://ftp.mirrorservice.org/sites/sourceware.org/pub/gcc/releases/gcc-4.8.4/gcc-4.8.4.tar.bz2 && \
    tar xvfj gcc-4.8.4.tar.bz2 && \
    cd gcc-4.8.4 && \
    ./configure --disable-multilib --enable-languages=c,c++,fortran && \
    make -j4 && make install && \
    cd / && rm -rf /code_gcc

RUN yum install -y cmake which zlib zlib-devel krb5-devel krb5-libs krb5-appl-clients
RUN git clone --depth 1 https://github.com/xrootd/xrootd.git -b stable-4.2.x  && \
    cd xrootd && \
    mkdir xrootd-build && \
    cd xrootd-build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local -DENABLE_PERL=FALSE -DENABLE_FUSE=FALSE && \
    make && make install && \
    cd / && rm -rf xrootd

RUN curl -O http://eos.cern.ch/rpms/eos-aquamarine/slc-6-x86_64/eos-client-0.3.84-aquamarine.slc6.x86_64.rpm && \
    yum -y localinstall eos-client-0.3.84-aquamarine.slc6.x86_64.rpm && \
    rm eos-client-0.3.84-aquamarine.slc6.x86_64.rpm

RUN echo "/usr/local/lib" >> /etc/ld.so.conf.d/local.conf && \
    echo "/usr/local/lib64" >> /etc/ld.so.conf.d/local.conf && \
    ldconfig  

ENV CC /usr/local/bin/gcc
ENV CXX /usr/local/bin/g++

RUN git clone --quiet http://root.cern.ch/git/root.git /code/root-v6-02-12 && \
    cd  /code/root-v6-02-12 && \
    git checkout v6-02-12 && \
    mkdir rootbuild && cd rootbuild && \
    cmake ..  -Droofit=ON -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j4 && \
    cmake --build . --target install && \
    cd / && rm -rf /code/root-v6-02-12
