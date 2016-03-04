FROM lukasheinrich/preasg-base

RUN git clone --quiet http://root.cern.ch/git/root.git /code/root-v6-02-12 && \
    cd  /code/root-v6-02-12 && \
    git checkout v6-02-12 && \
    mkdir rootbuild && cd rootbuild && \
    cmake ..  -Dall=ON -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j4 && \
    cmake --build . --target install && \
    cd / && rm -rf /code/root-v6-02-12
ENV ROOTSYS /usr/local
