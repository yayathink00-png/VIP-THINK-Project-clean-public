import Foundation
import Security

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

guard CommandLine.arguments.count == 4 else {
    fail("usage: xhs_keychain_helper <store|read> <service> <account>")
}

let operation = CommandLine.arguments[1]
let service = CommandLine.arguments[2]
let account = CommandLine.arguments[3]
let query: [CFString: Any] = [
    kSecClass: kSecClassGenericPassword,
    kSecAttrService: service,
    kSecAttrAccount: account,
]

if operation == "store" {
    let value = FileHandle.standardInput.readDataToEndOfFile()
    guard !value.isEmpty else { fail("empty value") }
    SecItemDelete(query as CFDictionary)
    var addQuery = query
    addQuery[kSecValueData] = value
    let status = SecItemAdd(addQuery as CFDictionary, nil)
    guard status == errSecSuccess else { fail("SecItemAdd failed: \(status)") }
} else if operation == "read" {
    var readQuery = query
    readQuery[kSecReturnData] = true
    readQuery[kSecMatchLimit] = kSecMatchLimitOne
    var result: CFTypeRef?
    let status = SecItemCopyMatching(readQuery as CFDictionary, &result)
    guard status == errSecSuccess, let data = result as? Data else { fail("SecItemCopyMatching failed: \(status)") }
    FileHandle.standardOutput.write(data)
} else {
    fail("unsupported operation")
}
