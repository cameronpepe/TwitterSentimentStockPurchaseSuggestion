var app=angular.module('myApp',['ngRoute']);
app.config(function($routeProvider){
    $routeProvider
        .when('/',{
            templateUrl: '../static/pages/home.html',
            controller: 'HomeController'
        })
        .when('/result',{
            templateUrl: '../static/pages/results.html',
            controller: 'ResultsController'
        });
});
app.factory('MyService', function() {
    // private
    var value = "";
    // public
    return {
      getValue: function() {
        return value;
      },
      
      setValue: function(val) {
        value = val;
      }
    };
});

app.controller('HomeController',function($scope, $http, $location, $rootScope, MyService){
    $scope.company = function(company) {
      console.log(company);
      if (company == 'Nike' || company == 'Facebook'){
        MyService.setValue(company);
        $rootScope.$broadcast('increment-value-event');
        var data = $.param({
            name: company
        });
          
        var config = {
            headers : {
                'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'
            }
        }
        console.log("THIS IS THE DATA")
        console.log(data);
        $http.post('/sendSNS', data, config)
        .success(function (data, status, headers, config) {
            $scope.PostDataResponse = data;
            $location.path('/result')
        })
        .error(function (data, status, header, config) {
            $scope.ResponseDetails = "Data: " + data +
                "<hr />status: " + status +
                "<hr />headers: " + header +
                "<hr />config: " + config;
            console.log($scope.ResponseDetails);
        });
      }
    };
});
app.controller('ResultsController', function($scope, $http, $location, MyService){
    $scope.value = MyService.getValue();
    $scope.showYes = false;
    $scope.showNo = false;
    $scope.showMaybe = false;
    
    $scope.short_conf = 0;
    $scope.mid_conf = 0;
    $scope.long_conf = 0;
    
    $scope.buy_short = "";
    $scope.buy_mid = "";
    $scope.buy_long = "";
    $scope.$on('increment-value-event', function() {    
      $scope.value = MyService.getValue();
    });
    $scope.loadValue = function() {
      $http.get('/getResult')
      .success(function (data) {
          console.log(data);
          var total = Number(data['short']['prediction']) + Number(data['mid']['prediction']) + Number(data['long']['prediction']);
          console.log(total);
          if (total >= 2) {
            $scope.showYes = true;
            $scope.showNo = false;
            $scope.showMaybe = false;
          }else if(total == 1){
            $scope.showMaybe = true;
            $scope.showYes = false;
            $scope.showNo = false;
          }
          else {
            $scope.showMaybe = false;
            $scope.showYes = false;
            $scope.showNo = true;
          }
          $scope.short_conf = Math.round(Number(data['short']['confidence'])*100, 1);
          $scope.mid_conf = Math.round(Number(data['mid']['confidence'])*100, 1);
          $scope.long_conf = Math.round(Number(data['long']['confidence'])*100, 1);
          
          
          if (Number(data['short']['prediction']) == 1){
            $scope.buy_short = "buy";
          }else{
            $scope.buy_short = "not buy";
          }
          if (Number(data['mid']['prediction']) == 1){
            $scope.buy_mid = "buy";
          }else{
            $scope.buy_mid = "not buy";
          }
          if (Number(data['long']['prediction']) == 1){
            $scope.buy_long = "buy";
          }else{
            $scope.buy_long = "not buy";
          }
      })
    };
    $scope.loadValue();
});
