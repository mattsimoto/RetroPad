#include <atomic>
#include <chrono>
#include <csignal>
#include <iostream>
#include <mutex>
#include <set>
#include <sstream>
#include <string>
#include <thread>
#include <pqrs/karabiner/driverkit/virtual_hid_device_driver.hpp>
#include <pqrs/karabiner/driverkit/virtual_hid_device_service.hpp>

namespace {
std::atomic<bool> exit_flag(false);
}

int main() {
  std::signal(SIGINT, [](int) { exit_flag = true; });
  pqrs::dispatcher::extra::initialize_shared_dispatcher();

  std::mutex client_mutex;
  auto client = std::make_unique<pqrs::karabiner::driverkit::virtual_hid_device_service::client>();
  std::atomic<bool> keyboard_ready(false);
  std::set<uint16_t> held;

  client->warning_reported.connect([](auto&& message) {
    std::cerr << "WARN " << message << std::endl;
  });
  client->connect_failed.connect([](auto&& code) {
    std::cout << "CONNECT_FAILED " << code << std::endl;
  });
  client->error_occurred.connect([](auto&& code) {
    std::cout << "ERROR " << code << std::endl;
  });
  client->connected.connect([&client] {
    pqrs::karabiner::driverkit::virtual_hid_device_service::virtual_hid_keyboard_parameters parameters;
    parameters.set_country_code(pqrs::hid::country_code::us);
    client->async_virtual_hid_keyboard_initialize(parameters);
  });
  client->virtual_hid_keyboard_ready.connect([&](auto&& ready) {
    keyboard_ready = ready;
    std::cout << (ready ? "READY" : "NOT_READY") << std::endl;
  });

  client->async_start();

  auto post = [&] {
    if (!keyboard_ready || !client) return;
    pqrs::karabiner::driverkit::virtual_hid_device_driver::hid_report::keyboard_input report;
    for (auto usage : held) report.keys.insert(usage);
    std::lock_guard<std::mutex> lock(client_mutex);
    if (client) client->async_post_report(report);
  };

  std::string line;
  while (!exit_flag && std::getline(std::cin, line)) {
    if (line == "QUIT") break;
    std::istringstream ss(line);
    std::string op;
    unsigned int usage = 0;
    ss >> op;
    if (op == "CLEAR") {
      held.clear();
      post();
      std::cout << "OK" << std::endl;
      continue;
    }
    ss >> usage;
    if (!ss || usage > 0xffff) {
      std::cout << "BAD_COMMAND" << std::endl;
      continue;
    }
    if (op == "DOWN") held.insert(static_cast<uint16_t>(usage));
    else if (op == "UP") held.erase(static_cast<uint16_t>(usage));
    else {
      std::cout << "BAD_COMMAND" << std::endl;
      continue;
    }
    post();
    std::cout << "OK" << std::endl;
  }

  held.clear();
  post();
  {
    std::lock_guard<std::mutex> lock(client_mutex);
    client = nullptr;
  }
  std::this_thread::sleep_for(std::chrono::milliseconds(200));
  pqrs::dispatcher::extra::terminate_shared_dispatcher();
  return 0;
}
