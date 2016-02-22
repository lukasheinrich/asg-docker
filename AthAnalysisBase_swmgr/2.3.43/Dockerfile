#FROM lukasheinrich/slc6_cern_server_x86_64_2015-02-10
FROM lukasheinrich/preasg-base
RUN yum groupinstall -y "Development Tools"
RUN yum install -y gcc libmpc-devel mpfr-devel gmp-devel tar bzip2 wget which
RUN mkdir /code
WORKDIR /code
RUN wget -q --no-check-certificate https://pc-ads-01.roma1.infn.it/KV/sw-mgr
RUN chmod +x ./sw-mgr
ENV ROOTDIR /code
RUN ./sw-mgr -a gcc-x86_64:4.9.3 -i  4.9.3 -n -o \
    --no-tag -p $ROOTDIR/atlas-gcc/493/x86_64 \
    --site-config $ROOTDIR/AtlasSiteConfig.sh
RUN ./sw-mgr -a AthAnalysisBase:2.3.43 -i 2.3.43 \
    -p $ROOTDIR/software/AthAnalysisBase/x86_64-slc6-gcc49-opt/2.3.43 \
    -T release --site-config $ROOTDIR/AtlasSiteConfig.sh \
    --no-tag --relative-links
RUN ln -s /lib64/libuuid.so.1 /lib64/libuuid.so
