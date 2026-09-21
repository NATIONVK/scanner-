from datetime import datetime
import socket
import threading
import sys

# ইনপুট নেওয়া
target_host = input("স্ক্যান করার জন্য আইপি বা ডোমেইন লিখুন: ")

try:
    target_ip = socket.gethostbyname(target_host)
except socket.gaierror:
    print("\n[!] ত্রুটি: ডোমেইন বা আইপি খুঁজে পাওয়া যায়নি।")
    sys.exit()

print("-" * 60)
print(f"টার্গেট লক্ষ্যবস্তু: {target_ip}")
print(f"স্ক্যান শুরু হওয়ার সময়: {datetime.now()}")
print("-" * 60)

# লক ব্যবহার করা যাতে প্রিন্ট করার সময় টেক্সটগুলো একসাথে পেঁচিয়ে না যায়
print_lock = threading.Lock()

def scan_port(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(0.5)
        result = s.connect_ex((target_ip, port))
        if result == 0:
            with print_lock:
                print(f"[+] পোর্ট {port}: খোলা (Open)")
        s.close()
    except:
        pass

# থ্রেডিং ব্যবহার করে দ্রুত স্ক্যান করা (১ থেকে ১০০০ পোর্ট)
print("স্ক্যান চলছে, অনুগ্রহ করে অপেক্ষা করুন...\n")
start_time = datetime.now()

threads = []
for port in range(1, 1001): # এখানে আপনার প্রয়োজনমতো পোর্ট রেঞ্জ বাড়াতে পারেন
    t = threading.Thread(target=scan_port, args=(port,))
    threads.append(t)
    t.start()

# সব থ্রেড শেষ হওয়া পর্যন্ত অপেক্ষা করা
for t in threads:
    t.join()

end_time = datetime.now()
total_time = end_time - start_time

print("-" * 60)
print(f"স্ক্যান সম্পন্ন হয়েছে!")
print(f"মোট সময় লেগেছে: {total_time}")
print("-" * 60)
