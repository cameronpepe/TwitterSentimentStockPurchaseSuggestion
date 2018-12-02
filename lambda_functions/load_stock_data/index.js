var mysql = require("mysql");
var moment = require('moment');
const alpha = require('alphavantage')({ key: 'PPXH5DYN5VS7EBD2' }); // Alpha Vantage API key: PPXH5DYN5VS7EBD2

let company = "Adidas";

// can also make the symbols object like below
let symbols = {
    "Nike": {
        "symbol" : "NYSE:NKE"
    },
    "Adidas": {
        "symbol" : "ADDYY"
    },
    "Facebook": {
        "symbol" : "NASDAQ:FB"
    },
    "Microsoft": {
        "symbol" : "NASDAQ:MSFT"
    }
};

// set up RDS first
var pool = mysql.createPool({
        connectionLimit :   1000,
        host     : "",
        user     : "",
        password : "",
        database : "",
        port     : ""
    });



function getTimeFrame() {
    // Decide what data range we'd like, can do daily, weekly, monthly
    // for up to 20 years historical data

    var today = new Date.now();
    var days = new Date("2018-10-29")  // some date
    var diff = Math.abs(today - days);
    
    return days;

}


function loadAndStoreStocks(days) {
    // https://www.alphavantage.co/    
    let fullData = [];

    // loop through just this company to get and save stock data
    alpha.data.daily(symbols[company]["symbol"], "full", "json", "30min").then(data => {
        fullData = data; // save returned JSON response
        
        let allKeys = Object.keys(fullData['Time Series (Daily)']);
        
        var vals = []
        for (const key of allKeys) {
            let open = fullData['Time Series (Daily)'][key]['1. open'];
            let high = fullData['Time Series (Daily)'][key]['2. high'];
            let low = fullData['Time Series (Daily)'][key]['3. low'];
            let close = fullData['Time Series (Daily)'][key]['4. close'];
            let volume = fullData['Time Series (Daily)'][key]['5. volume'];
                
            let f_timestamp = new Date(); // store time
            var timestamp = moment(f_timestamp, 'ddd MMM DD HH:mm:ss +ZZ YYYY').format('YYYY-MM-DD h:mm:ss');
            
            var sql = "INSERT IGNORE INTO stockData (timestamp, date, symbol, company, open, high, low, close, volume) VALUES ?";
            var values =[timestamp, key, symbols[company]['symbol'], company, open, high, low, close, volume];
            console.log(values);
            vals.push(values);

        
        }
        pool.query(sql, [vals], function (err, result) {
            if (err) throw err;
            console.log("Number of records inserted: " + result.affectedRows);
        });
        
        
    });
}

function processEvent() {
    getTimeFrame()
        .then(days => loadAndStoreStocks(days))
}


loadAndStoreStocks(1840);
