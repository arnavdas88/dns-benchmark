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
    "default",
    # "103.154.234.109"
]
def benchmark(console: Console,  additional_domains: list[str], additional_servers: list[str], N = 50, time_unit = "ms", timeout = 5.0) -> float:

    all_domains_to_benchmark = DOMAIN + additional_domains
    all_servers_to_benchmark = SERVER + additional_servers

    time_unit = TimeUnit[time_unit] if type(time_unit) is str else time_unit

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
                try:
                    if server != "default":
                        msg = dns.message.make_query(host, "A")
                        start = time.perf_counter_ns()
                        dns.query.udp(msg, server, timeout=timeout)
                        end = time.perf_counter_ns()
                    else:
                        start = time.perf_counter_ns()
                        dns.resolver.resolve(host, 'A', lifetime=timeout)
                        end = time.perf_counter_ns()
                    benchmark_bucket[server][host].append(end - start)
                    benchmark_server_bucket[server].append(end - start)
                except dns.exception.Timeout as ex:
                    benchmark_bucket[server][host].append(np.nan)
                    benchmark_server_bucket[server].append(np.nan)
        data = humanize_server_bucket(benchmark_server_bucket, )

        sorted_data = sorted(data, key=lambda data: data['mean'])

        table = make_table(sorted_data, entries = f" ( {i+1} / {N} ) ", unit = time_unit, roundoff=2)
        console.update(table, refresh=True)
    return benchmark_server_bucket, table

def humanize_server_bucket(server_bucket, ):
    server_bucket_npy = {server: np.array(latency) for server, latency in server_bucket.items() }
    # server_bucket_sec = {server: latency / 1e9 for server, latency in server_bucket_npy.items() }
    # server_bucket_clean = {server: latency[~np.isnan(latency)] for server, latency in server_bucket_npy.items() }
    server_bucket_sec_without_outliers = {server: reject_outliers(latency) for server, latency in server_bucket_npy.items() }
    return [ 
        {
            "server": server, 
            "mean": latency.mean() if len(latency) else 0, 
            "max": latency.max() if len(latency) else 0, 
            "min": latency.min() if len(latency) else 0, 
            "stddev": latency.std() if len(latency) else 0, 
            "p99": np.percentile(latency, 99) if len(latency) else 0,
            "p95": np.percentile(latency, 95) if len(latency) else 0,
            "outliers": len(outliers),
            "errors": len(nan_data[nan_data])
        } for server, (outliers, latency, nan_data) in server_bucket_sec_without_outliers.items() 
    ]

def reject_outliers(data, iqr=0.9):
    nan_data = np.isnan(data)
    data = data[~nan_data]
    if len(data) == 0:
        return np.array([]), np.array([]), nan_data

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


    return outliers, iqr_data, nan_data

def make_table(sorted_data, entries = None, unit = TimeUnit.ms, roundoff = 5):
    entries = entries if entries else ""
    # 3. Create the table
    table = Table(title=f"DNS Resolver Performance {entries}",  box=box.SIMPLE)
    table.add_column("Server")
    table.add_column(f"Min ({unit.name})")
    table.add_column(f"Mean ({unit.name})")
    table.add_column("Std Dev")
    table.add_column(f"Max ({unit.name})")
    table.add_column("P95")
    table.add_column("P99")
    table.add_column("Outliers")
    table.add_column("Errors")

    # 4. Add the *sorted* rows to the table
    for data in sorted_data:
        table.add_row(
            data["server"],
            str(np.round(data["min"] / unit.value, decimals=roundoff)),
            str(np.round(data["mean"] / unit.value, decimals=roundoff)),
            str(np.round(data["stddev"] / unit.value, decimals=roundoff)),
            str(np.round(data["max"] / unit.value, decimals=roundoff)),
            str(np.round(data["p95"] / unit.value, decimals=roundoff)),
            str(np.round(data["p99"] / unit.value, decimals=roundoff)),
            str(data["outliers"]),
            str(data["errors"]),
        )
    return table