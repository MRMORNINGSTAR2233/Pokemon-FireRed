-- mGBA Simple Controller for AI Pokemon Player
-- This script uses file-based communication (more reliable than sockets)
-- Load this script in mGBA: Tools > Scripting > Load Script

local COMMAND_FILE = "/tmp/mgba_command.txt"
local RESPONSE_FILE = "/tmp/mgba_response.txt"
local SCREEN_FILE = "/tmp/mgba_screen.png"

-- Logging function
local function log(message)
    console:log("[AI-Pokemon] " .. message)
end

-- Clear any existing files
local function clearFiles()
    os.remove(COMMAND_FILE)
    os.remove(RESPONSE_FILE)
end

-- Read command from file
local function readCommand()
    local file = io.open(COMMAND_FILE, "r")
    if file then
        local content = file:read("*all")
        file:close()
        if content and content ~= "" then
            os.remove(COMMAND_FILE)  -- Delete after reading
            return content:gsub("[\r\n]", "")  -- Remove newlines
        end
    end
    return nil
end

-- Write response to file
local function writeResponse(response)
    local file = io.open(RESPONSE_FILE, "w")
    if file then
        file:write(response)
        file:close()
    end
end

-- Track button presses for auto-release
local pressedButtons = {}
local framesSincePress = {}

-- Handle incoming commands
local function handleCommand(cmd)
    if not cmd or cmd == "" then
        return nil
    end
    
    local parts = {}
    for part in string.gmatch(cmd, "[^|]+") do
        table.insert(parts, part)
    end
    
    local action = parts[1]
    log("Command: " .. action)
    
    if action == "BUTTON" then
        local button = parts[2]
        local state = parts[3] or "1"
        
        local buttonMap = {
            ["A"] = 0, ["B"] = 1, ["SELECT"] = 2, ["START"] = 3,
            ["RIGHT"] = 4, ["LEFT"] = 5, ["UP"] = 6, ["DOWN"] = 7,
            ["R"] = 8, ["L"] = 9
        }
        
        local key = buttonMap[string.upper(button)]
        if key then
            if state == "1" or state == "press" then
                emu:addKey(key)
                log("Pressed: " .. button)
            else
                emu:clearKey(key)
                log("Released: " .. button)
            end
            return "OK"
        end
        return "ERROR:Unknown button"
        
    elseif action == "TAP" then
        -- Tap = press for a few frames then release
        local button = parts[2]
        local buttonMap = {
            ["A"] = 0, ["B"] = 1, ["SELECT"] = 2, ["START"] = 3,
            ["RIGHT"] = 4, ["LEFT"] = 5, ["UP"] = 6, ["DOWN"] = 7,
            ["R"] = 8, ["L"] = 9
        }
        local key = buttonMap[string.upper(button)]
        if key then
            emu:addKey(key)
            pressedButtons[key] = true
            framesSincePress[key] = 0
            log("Tapped: " .. button)
            return "OK"
        end
        return "ERROR:Unknown button"
        
    elseif action == "RELEASE_ALL" then
        for i = 0, 9 do
            emu:clearKey(i)
            pressedButtons[i] = nil
        end
        return "OK"
        
    elseif action == "SCREENSHOT" then
        emu:screenshot(SCREEN_FILE)
        log("Screenshot saved")
        return "OK:" .. SCREEN_FILE
        
    elseif action == "READ" then
        local addr = tonumber(parts[2], 16) or tonumber(parts[2])
        local len = tonumber(parts[3]) or 1
        
        if addr then
            local result = {}
            for i = 0, len - 1 do
                local byte = emu:read8(addr + i)
                table.insert(result, string.format("%02X", byte))
            end
            return "OK:" .. table.concat(result, "")
        end
        return "ERROR:Invalid address"
        
    elseif action == "PAUSE" then
        emu:pause()
        return "OK:PAUSED"
        
    elseif action == "RESUME" then
        emu:unpause()
        return "OK:RESUMED"
        
    elseif action == "RESET" then
        emu:reset()
        return "OK:RESET"
        
    elseif action == "SAVE" then
        local slot = tonumber(parts[2]) or 1
        emu:saveStateSlot(slot)
        log("Saved state to slot " .. slot)
        return "OK:" .. slot
        
    elseif action == "LOAD" then
        local slot = tonumber(parts[2]) or 1
        emu:loadStateSlot(slot)
        log("Loaded state from slot " .. slot)
        return "OK:" .. slot
        
    elseif action == "PING" then
        return "PONG"
        
    else
        return "ERROR:Unknown command"
    end
end

local HOLD_FRAMES = 8

-- Frame callback
callbacks:add("frame", function()
    -- Auto-release buttons after holding for HOLD_FRAMES
    for key, pressed in pairs(pressedButtons) do
        if pressed then
            framesSincePress[key] = (framesSincePress[key] or 0) + 1
            if framesSincePress[key] > HOLD_FRAMES then
                emu:clearKey(key)
                pressedButtons[key] = nil
                framesSincePress[key] = nil
            end
        end
    end
    
    -- Check for commands
    local cmd = readCommand()
    if cmd then
        local response = handleCommand(cmd)
        if response then
            writeResponse(response)
        end
    end
end)

-- Initialization
log("========================================")
log(" AI Pokemon Player - mGBA Controller")
log("========================================")
log("")
log("Commands via: " .. COMMAND_FILE)
log("Responses at: " .. RESPONSE_FILE)
log("Screenshots:  " .. SCREEN_FILE)
log("")
clearFiles()
log("Ready! Waiting for commands...")
log("")
