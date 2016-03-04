FROM lukasheinrich/preasg-base
RUN mkdir /code
WORKDIR /code
RUN yum install -y wget
RUN curl -skO https://pc-ads-01.roma1.infn.it/KV/sw-mgr
RUN chmod +x ./sw-mgr
ENV ROOTDIR /code
RUN ./sw-mgr -a gcc-x86_64:4.9.3 -i  4.9.3 -n -o \
    --no-tag -p $ROOTDIR/atlas-gcc/493/x86_64 \
    --site-config $ROOTDIR/AtlasSiteConfig.sh
RUN ./sw-mgr -a AthAnalysisBase:2.3.45 -i 2.3.45 \
    -p $ROOTDIR/software/AthAnalysisBase/x86_64-slc6-gcc49-opt/2.3.45 \
    -T release --site-config $ROOTDIR/AtlasSiteConfig.sh \
    --no-tag --relative-links
RUN ln -s /lib64/libuuid.so.1 /lib64/libuuid.so
RUN ln -s /usr/local/bin/g++ /usr/local/bin/lcg-g++-4.9.3
