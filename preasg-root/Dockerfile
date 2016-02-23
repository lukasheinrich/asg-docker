FROM lukasheinrich/preasg-base

RUN yum groupinstall -y "Development Tools"
RUN yum install -y gcc libmpc-devel mpfr-devel gmp-devel tar bzip2
RUN mkdir /code_gcc && cd /code_gcc && \
    curl ftp://ftp.mirrorservice.org/sites/sourceware.org/pub/gcc/releases/gcc-4.9.3/gcc-4.9.3.tar.bz2 -O && \
    tar xvfj gcc-4.9.3.tar.bz2 && \
    cd gcc-4.9.3 && \
    ./configure --disable-multilib --enable-languages=c,c++,fortran && \
    make -j2 && make install && \
    cd / && rm -rf /code_gcc


RUN echo "/usr/local/lib" >> /etc/ld.so.conf.d/local.conf && \
    echo "/usr/local/lib64" >> /etc/ld.so.conf.d/local.conf && \
    ldconfig  


#required packages for ROOT
RUN yum install -y git make binutils libX11-devel libXpm-devel libXft-devel libXext-devel

#optional packages
RUN yum install -y openssl-devel pcre-devel mesa-libGL-devel mesa-libGLU-devel glew-devel \
        ftgl-devel mysql-devel fftw-devel cfitsio-devel graphviz-devel avahi-compat-libdns_sd-devel \
        libldap-dev python-devel libxml2-devel gsl-static

ENV ROOTSYS /usr/local
RUN echo "/usr/local/lib" >> /etc/ld.so.conf.d/local.conf && \
    echo "/usr/local/lib64" >> /etc/ld.so.conf.d/local.conf && \
    ldconfig

RUN git clone --quiet http://root.cern.ch/git/root.git /code/root-v6-02-12 &&\
    cd  /code/root-v6-02-12 &&\
    git checkout v6-02-12 &&\
    ./configure --all &&\
    make -j4 &&\
    make -j4 install &&\
    cd / &&\
    rm -rf /code
