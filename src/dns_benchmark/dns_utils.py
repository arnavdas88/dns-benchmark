import time
import statistics
import numpy as np

import dns.resolver

from rich import box
from rich.console import Console
from rich.table import Table


import enum
class TimeUnit(enum.IntEnum):
    s = 1e9
    ms = 1e6
    us = 1e3
    ns = 1


DOMAIN = [
    "google.com"
]
SERVER = [
    "8.8.8.8",
    "1.1.1.1",
    "9.9.9.9",
    "default"
]
def benchmark(console: Console,  additional_domains: list[str], N = 50) -> float:

    all_domains_to_benchmark = DOMAIN + additional_domains
    # console.print(all_domains_to_benchmark)

    all_servers_to_benchmark = SERVER
    # console.print(all_domains_to_benchmark)

    benchmark_bucket = {}
    benchmark_server_bucket = {}

    for server in all_servers_to_benchmark:
        benchmark_bucket[server] = {}
        benchmark_server_bucket[server] = []

    for server in all_servers_to_benchmark:
        for host in all_domains_to_benchmark:
            benchmark_bucket[server][host] = []
        
    for i in range(N):
        for server in all_servers_to_benchmark:
            for host in all_domains_to_benchmark:
                if server != "default":
                    msg = dns.message.make_query(host, "A")
                    start = time.perf_counter_ns()
                    dns.query.udp(msg, server)
                    end = time.perf_counter_ns()
                else:
                    start = time.perf_counter_ns()
                    dns.resolver.resolve(host, 'A')
                    end = time.perf_counter_ns()
                benchmark_bucket[server][host].append(end - start)
                benchmark_server_bucket[server].append(end - start)
        data = humanize_server_bucket(benchmark_server_bucket, )

        sorted_data = sorted(data, key=lambda data: data['mean'])

        # console.clear()
        # console.print(make_table(sorted_data))

        console.update(make_table(sorted_data, unit = TimeUnit.us, roundoff=2), refresh=True)
    return

def humanize_server_bucket(server_bucket, ):
    server_bucket_npy = {server: np.array(latency) for server, latency in server_bucket.items() }
    # server_bucket_sec = {server: latency / 1e9 for server, latency in server_bucket_npy.items() }
    server_bucket_sec = {server: latency for server, latency in server_bucket_npy.items() }
    server_bucket_sec_without_outliers = {server: reject_outliers(latency) for server, latency in server_bucket_sec.items() }
    return [ 
        {
            "server": server, 
            "mean": latency.mean(), 
            "max": latency.max(), 
            "min": latency.min(), 
            "stddev": latency.std(), 
            "p99": np.percentile(latency, 99),
            "p95": np.percentile(latency, 95),
        } for server, latency in server_bucket_sec_without_outliers.items() 
    ]

def reject_outliers(data, iqr=0.9):
    lower_percentile = (1 - iqr) / 2 
    upper_percentile = 1 - (1 - iqr) / 2 

    # Calculate Q1 and Q3
    q1 = np.percentile(data, 100 * lower_percentile)
    q3 = np.percentile(data, 100 * upper_percentile)

    # Calculate IQR
    iqr = q3 - q1

    # Define outlier bounds
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # Identify outliers
    outliers = data[(data < lower_bound) | (data > upper_bound)]
    iqr_data = data[(data > lower_bound) & (data < upper_bound)]

    return iqr_data

def make_table(sorted_data, unit = TimeUnit.ms, roundoff = 5):
    # 3. Create the table
    table = Table(title=f"DNS Resolver Performance ({unit.name})",  box=box.SIMPLE)
    table.add_column("Server")
    table.add_column("Min")
    table.add_column("Mean")
    table.add_column("Std Dev")
    table.add_column("Max")
    table.add_column("P95")
    table.add_column("P99")

    # 4. Add the *sorted* rows to the table
    for data in sorted_data:
        table.add_row(
            data["server"],
            str(np.round(data["min"] / unit.value, decimals=roundoff)),
            str(np.round(data["mean"] / unit.value, decimals=roundoff)),
            str(np.round(data["stddev"] / unit.value, decimals=roundoff)),
            str(np.round(data["max"] / unit.value, decimals=roundoff)),
            str(np.round(data["p95"] / unit.value, decimals=roundoff)),
            str(np.round(data["p99"] / unit.value, decimals=roundoff))
        )
    return table