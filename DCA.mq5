
//+------------------------------------------------------------------+
//|                                                RandomTradeEA.mq5 |
//| Opens random trade, adds more on -$5 loss of last trade,         |
//| stops and closes all when +$5 profit is reached                  |
//+------------------------------------------------------------------+
#property copyright "ChatGPT"
#property version   "1.01"
#property strict

input double lot_size      = 0.1;    // Lot size for each trade
input double loss_trigger  = 5.0;    // $ loss on last trade to open new one
input double profit_target = 5.0;    // $ profit to close all trades
input ENUM_TIMEFRAMES tf  = PERIOD_CURRENT;
int magic_number = 123456;

bool trade_direction_set = false;
ENUM_ORDER_TYPE direction;          // Will hold buy or sell direction

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
Print("RandomTradeEA started.");
return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
Print("RandomTradeEA stopped.");

double floating_profit = 0.0;
int open_positions = 0;

for(int i = PositionsTotal() - 1; i >= 0; i--)
{
ulong ticket = PositionGetTicket(i);
if(PositionSelectByTicket(ticket) && PositionGetInteger(POSITION_MAGIC) == magic_number)
{
double profit = PositionGetDouble(POSITION_PROFIT);
floating_profit += profit;
open_positions++;

// Close the position  
     ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);  
     double volume = PositionGetDouble(POSITION_VOLUME);  
     double price = (pos_type == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);  

     MqlTradeRequest request;  
     MqlTradeResult result;  
     ZeroMemory(request);  
     ZeroMemory(result);  

     request.action = TRADE_ACTION_DEAL;  
     request.position = ticket;  
     request.volume = volume;  
     request.magic = magic_number;  
     request.symbol = _Symbol;  
     request.deviation = 10;  
     request.type = (pos_type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;  
     request.price = price;  

     if(!OrderSend(request, result))  
        Print("Failed to close position #", ticket, " on deinit. Error: ", GetLastError());  
     else if(result.retcode != TRADE_RETCODE_DONE)  
        Print("Close order on deinit failed retcode: ", result.retcode);  
     else  
        Print("Position #", ticket, " closed on deinit.");  
  }

}

double closed_profit = AccountInfoDouble(ACCOUNT_PROFIT);
double net_profit = closed_profit + floating_profit;

Print("=== Final Log on EA Stop ===");
Print("Closed Profit: $", DoubleToString(closed_profit, 2));
Print("Floating Profit (before forced close): $", DoubleToString(floating_profit, 2));
Print("Net Profit (Closed + Floating): $", DoubleToString(net_profit, 2));
Print("=============================");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
double total_profit = 0.0;
int total_positions = PositionsTotal();
int ea_positions_count = 0;

for(int i = 0; i < total_positions; i++)
{
ulong ticket = PositionGetTicket(i);
if(PositionSelectByTicket(ticket) && PositionGetInteger(POSITION_MAGIC) == magic_number)
{
total_profit += PositionGetDouble(POSITION_PROFIT);
ea_positions_count++;
}
}

// Close all if profit target reached
if(total_profit >= profit_target)
{
CloseAllTrades();
Print("Profit target reached. All trades closed.");
trade_direction_set = false;
}

// Open initial trade randomly
if(!trade_direction_set)
{
direction = (MathRand() % 2 == 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
if(OpenTrade(direction))
{
trade_direction_set = true;
Print("Initial trade opened: ", EnumToString(direction));
}
else
{
Print("Failed to open initial trade.");
}
return;
}

// Open new trade if last trade has $5 loss
ulong last_ticket = GetLastTradeTicket();
if(last_ticket != 0)
{
double last_loss = GetTradeProfitByTicket(last_ticket);
if(last_loss <= -loss_trigger)
{
if(OpenTrade(direction))
Print("Additional trade opened due to last trade loss >= $5.");
else
Print("Failed to open additional trade.");
}
}
}

//+------------------------------------------------------------------+
//| Open trade function                                              |
//+------------------------------------------------------------------+
bool OpenTrade(ENUM_ORDER_TYPE type)
{
MqlTradeRequest request;
MqlTradeResult result;
ZeroMemory(request);
ZeroMemory(result);

double price = (type == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);

request.action = TRADE_ACTION_DEAL;
request.symbol = _Symbol;
request.volume = lot_size;
request.type = type;
request.price = price;
request.deviation = 10;
request.magic = magic_number;
request.comment = "RandomTradeEA";
request.sl = 0;
request.tp = 0;

if(!OrderSend(request, result))
{
Print("OrderSend failed: ", GetLastError());
return false;
}
if(result.retcode != TRADE_RETCODE_DONE)
{
Print("OrderSend retcode: ", result.retcode);
return false;
}
return true;
}

//+------------------------------------------------------------------+
//| Close all trades opened by this EA                               |
//+------------------------------------------------------------------+
void CloseAllTrades()
{
int total_positions = PositionsTotal();

for(int i = total_positions - 1; i >= 0; i--)
{
ulong ticket = PositionGetTicket(i);
if(PositionSelectByTicket(ticket))
{
if(PositionGetInteger(POSITION_MAGIC) == magic_number)
{
ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
double volume = PositionGetDouble(POSITION_VOLUME);
double price = (pos_type == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);

MqlTradeRequest request;  
        MqlTradeResult result;  
        ZeroMemory(request);  
        ZeroMemory(result);  

        request.action = TRADE_ACTION_DEAL;  
        request.position = ticket;  
        request.volume = volume;  
        request.magic = magic_number;  
        request.symbol = _Symbol;  
        request.deviation = 10;  
        request.type = (pos_type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;  
        request.price = price;  

        if(!OrderSend(request, result))  
           Print("Failed to close position #", ticket, " error: ", GetLastError());  
        else if(result.retcode != TRADE_RETCODE_DONE)  
           Print("Close order failed retcode: ", result.retcode);  
        else  
           Print("Position #", ticket, " closed.");  
     }  
  }

}
}

//+------------------------------------------------------------------+
//| Helper: Get the last trade ticket by open time                   |
//+------------------------------------------------------------------+
ulong GetLastTradeTicket()
{
datetime latest_time = 0;
ulong last_ticket = 0;

for(int i = 0; i < PositionsTotal(); i++)
{
ulong ticket = PositionGetTicket(i);
if(PositionSelectByTicket(ticket))
{
if(PositionGetInteger(POSITION_MAGIC) == magic_number)
{
datetime opentime = (datetime)PositionGetInteger(POSITION_TIME);
if(opentime > latest_time)
{
latest_time = opentime;
last_ticket = ticket;
}
}
}
}
return last_ticket;
}

//+------------------------------------------------------------------+
//| Helper: Get floating profit/loss of a trade by ticket            |
//+------------------------------------------------------------------+
double GetTradeProfitByTicket(ulong ticket)
{
if(PositionSelectByTicket(ticket))
return PositionGetDouble(POSITION_PROFIT);
return 0.0;

}
//+------------------------------------------------------------------+