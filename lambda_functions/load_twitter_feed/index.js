let company;
var AWS = require('aws-sdk') //https://aws.amazon.com/sdk-for-node-js/
AWS.config.update({region:'us-east-1'});
var config = require('./config.js');
var mysql = require('mysql');

var Twitter = require('twitter'); // might be easier to make this a global variable, up to you
var config = require('./config.js');
var moment = require('moment');

var labels = require('./labels.json');
var Sentiment = require('sentiment');
var sentiment = new Sentiment();

var C = new AWS.Comprehend();
var COMPANY = "Adidas"
function getTimeFrame() {
    // look up the most recent tweet for this company
    // Finding out when most recent tweet was from RDS
    // see how many days back it is
    
    // max time frame is 6 months back (default to 6 months if most recent tweet is > 6 months away)

    // return the number of days
    var lastdate = "";
    var sql = "SELECT max(date) FROM tweetSentiment;";
    pool.query(sql, function (err, result) {
        if (err) throw err;
        console.log(result);
        var st = JSON.parse(JSON.stringify(result[0]));
        for (var key in st) {
            lastdate = st[key];
            console.log(lastdate);
        }
        
    })
    pool.end();
    console.log(lastdate);
}


function getSentiment(tweet, ts, cb) {
    // https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/Comprehend.html
    // https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/Comprehend.html#detectSentiment-property

    var result = sentiment.analyze(tweet);
    var compScore = result.comparative;
    var emotion = 'neutral';
    if (compScore > .3){
        emotion = 'positive';
    }
    if (compScore < -.3){
        emotion = 'negative'
    }

    // Calculate the individual postive or negative influences
    var posScore = 0;
    var negScore = 0;
    var neutralScore = 0;
    for(let i = 0; i < result.positive.length; i++){
        var tokenPos = result.positive[i];
        if(labels[tokenPos]){
            posScore = posScore + labels[tokenPos]
        }    
    }   
    for(let i = 0; i < result.negative.length; i++){
        var tokenNeg = result.positive[i];
        if(labels[tokenNeg]){
            negScore = negScore + labels[tokenNeg]
        }    
    }
    var numNeutral = (result.tokens.length - result.words.length);
    //console.log(numNeutral);
    neutralScore = numNeutral/result.tokens.length;
    posScore = posScore/result.tokens.length;
    negScore = negScore/result.tokens.length;
    // We've got relative scores, now just normalize all 3 values so they sum to 1
    /*var totalSentiment = neutralScore + posScore + negScore;
    neutralScore = neutralScore/totalSentiment;
    posScore = posScore/totalSentiment;
    negScore = negScore/totalSentiment;*/
    var totalSentiment = neutralScore + posScore + negScore;
    if(totalSentiment != 0){
    neutralScore = neutralScore/totalSentiment;
    posScore = posScore/totalSentiment;
    negScore = negScore/totalSentiment;
    }
    else{
        neutralScore = 0;
        posScore = 0;
        negScore = 0;
    }
    

    var output = {"neutralScore": neutralScore, "positiveScore": posScore, "negativeScore": negScore};
    cb(true, output, tweet, ts);

}

var sqlValues = [];
function sqlBouncer(isOk, text, timestamp, sentiment) {
    if (isOk) {
        // console.log(sentiment);
        var pos = sentiment['positiveScore'];
        var neg = sentiment['negativeScore'];
        var neutral = sentiment['neutralScore'];
        var date = timestamp.substring(0,10);
    
        var values = [timestamp, date, COMPANY, text, pos, neg, neutral];
        if (!sqlValues.includes(values)){ // inefficient asf
            sqlValues.push(values);
            if (sqlValues.length >= 100){ // this is less of a hack
                handToSQL();
            }
        }
        
    }
}

function handToSQL() {
    storeTweets(sqlValues);
    sqlValues = [];
}

function storeTweets(vals) {
    // store the text, timestamp, and sentiment in the RDS
    console.log(vals[0][1]);
    var sql = "INSERT IGNORE INTO tweetSentimentNew (timestamp, date, company, text, positive, negative, neutral) VALUES ?";
    pool.query(sql, [vals], function (err, result) {
        if (err) throw err;
    })
}
//Uses twitter API and gets only recent tweets
function loadAndProcessTweets(/*days*/) {
    //https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets
    //https://codeburst.io/build-a-simple-twitter-bot-with-node-js-in-just-38-lines-of-code-ed92db9eb078
    
    var T = new Twitter(config);
    var params = {
        q: '#Nike', //q is the only required parameter, and is looking for tweets with Nike
        count: 1, //only want X number of results
        result_type: 'recent', //only most recent results
        lang: 'en' //only English results
    }
    return;
    T.get('search/tweets', params, function(err, data, response){
        if(!err){
            for(let i = 0; i < data.statuses.length; i++){
            // Get the tweet Id from the returned data
            let id = { id: data.statuses[i].id_str }
            //console.log(data.statuses[i]);
            var text = data.statuses[i].text;
            var timestamp = data.statuses[i].created_at;
            var adjusted_timestamp = moment(timestamp, 'ddd MMM DD HH:mm:ss +ZZ YYYY').format('YYYY-MM-DD h:mm:ss');
            // console.log(adjusted_timestamp);
            var sentiment = getSentiment(data.statuses[i]); //this might change as getSentiment changes
            // storeTweets(text, adjusted_timestamp, sentiment, positive, negative, neutral, mixed);
            }
        } else {
            console.log(err);
        }
    })
}

var uint8arrayToString = function(data){
    return String.fromCharCode.apply(null, data);
};

//trying with Python function
function loadOldTweets(){
    var spawn = require('child_process').spawn,
    py = spawn('python', ['oldtweet.py', COMPANY, '182']); //365*5 = 1825
    py.stdout.on('data', function(data){
        var tweetResponse = data.toString();
        if (tweetResponse.includes("\n")) {
            var tweets = tweetResponse.split("\n")
            for (var i = 0; i < tweets.length - 1; i++) {
                var tweet = JSON.parse(tweets[i]);
                var text = tweet['text'];
                var ts = tweet['timestamp'];
                getSentiment(text, ts, function(isOk, data, text1, ts1) {
                    sqlBouncer(isOk, text1, ts1, data);
                });
            }
        } else {
            var text = tweet['text'];
            var ts = tweet['timestamp'];
            var tweet = JSON.parse(tweetResponse);
            getSentiment(text, ts, function(isOk, data, text1, ts1) {
                sqlBouncer(isOk, text1, ts1, data);
            });

        }
        
    });
    py.stderr.on('data', (data) => {
        console.log("PYTHON ERROR")
        console.log(uint8arrayToString(data));
    });
    py.stdout.on('end', function(){
        handToSQL();
    });
}

function processEvent() {
    getTimeFrame()
        .then(days => loadAndProcessTweets(days))
}


// exports.handler = async (event) => {
    
//     // console.log("Receied Event: ", event);
//     event = JSON.parse(event);
//     let message = event.Records[0].Sns.Message
//     company = message.company;
//     processEvent()
//         .then(() => {
//                 return 200
//             })

//     // const response = {
//     //     statusCode: 200,
//     //     body: JSON.stringify('Hello from Lambda!'),
//     // };
//     // return response;
// };
function temp_runner() {
    
    pool = mysql.createPool({
        connectionLimit :   1000,
        host     : "",
        user     : "",
        password : "",
        database : "",
        port     : ""
    });
    loadOldTweets();
}

temp_runner();
