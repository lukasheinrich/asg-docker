FROM lukasheinrich/slc6_cern_server_x86_64_2015-02-10
RUN mkdir /code_gcc
WORKDIR /code_gcc
RUN yum groupinstall -y "Development Tools" 
RUN yum install -y gcc libmpc-devel mpfr-devel gmp-devel tar bzip2
RUN yum install -y davix-libs
RUN curl ftp://ftp.mirrorservice.org/sites/sourceware.org/pub/gcc/releases/gcc-4.9.3/gcc-4.9.3.tar.bz2 -O
RUN tar xvfj gcc-4.9.3.tar.bz2
WORKDIR gcc-4.9.3
RUN ./configure --disable-multilib --enable-languages=c,c++,fortran
RUN make -j2 && make install
RUN mkdir /code
WORKDIR /code
RUN curl -o install.sh http://atlas-computing.web.cern.ch/atlas-computing/links/pacballs/AthAnalysisSUSY_2_3_41_x86_64_slc6_gcc49_opt.time-2016-01-21-18-58-03.md5-f9054eb657c11757b8f7988587caea69.sh
RUN chmod +x install.sh
RUN ./install.sh
# ADD susytest.sh susytest.sh
