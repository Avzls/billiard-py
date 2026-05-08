FROM nodered/node-red:3.1

COPY data/package.json /data/package.json
COPY data/flows.json /data/flows.json
RUN cd /data && npm install --unsafe-perm --no-update-notifier --no-fund --omit=dev
