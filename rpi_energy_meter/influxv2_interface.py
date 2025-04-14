"""
Module to write POINTS to an InfluxV2 Database
"""


from influxdb_client import InfluxDBClient, Point, WriteOptions
# from influxdb_client.client.write_api import SYNCHRONOUS
INFLUX_SIZE_BATCH :int = 500
INFLUX_INTERVAL_FLUSH :int = 10000
INFLUX_INTERVAL_JITTER :int = 2000
INFLUX_INTERVAL_RETRY :int = 5000


class infv2db:
    def __init__(self, token: str, organization: str, bucket: str, host = "localhost", port = 8086):
        self._db_host = "http://" + host + ":" + str(port)
        self._token = token
        self._org = organization
        self._bucket = bucket
        self.open()

    def open(self):
        self._db = InfluxDBClient(url=self._db_host, token=self._token, org=self._org, debug=False)
        self._db_write = self._db.write_api(
            write_options=WriteOptions(
                batch_size=INFLUX_SIZE_BATCH,
                flush_interval=INFLUX_INTERVAL_FLUSH,
                jitter_interval=INFLUX_INTERVAL_JITTER,
                retry_interval=INFLUX_INTERVAL_RETRY)
            )
        # self._db_write = self._db.write_api(write_options=SYNCHRONOUS)

    def write(self, points: list[Point]):
        self._db_write.write(self._bucket, self._org, points)

    def close(self):
        self._db.close()
